#import <Foundation/Foundation.h>
#include "acnh_user_data.h"
#include <CommonCrypto/CommonDigest.h>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <stdio.h>
#include <unistd.h>

static NSString *const bundle = @"com.nintendo.acnh.native";

static void fail(NSString *message) {
    @throw [NSException exceptionWithName:@"ACNHUserData" reason:message userInfo:nil];
}
static void check(BOOL ok, NSString *message) { if (!ok) fail(message); }
static NSString *child(NSString *path, NSString *name) { return [path stringByAppendingPathComponent:name]; }
static BOOL exists(NSString *path) {
    struct stat st;
    if (!lstat(path.fileSystemRepresentation, &st)) return YES;
    check(errno == ENOENT, [@"Cannot inspect " stringByAppendingString:path]); return NO;
}
static void directory(NSString *path) {
    NSError *error = nil;
    check([[NSFileManager defaultManager] createDirectoryAtPath:path withIntermediateDirectories:YES
            attributes:@{NSFilePosixPermissions:@0700} error:&error], error.localizedDescription ?: path);
    struct stat st;
    check(!lstat(path.fileSystemRepresentation, &st) && S_ISDIR(st.st_mode),
          [@"Expected a real directory: " stringByAppendingString:path]);
}
static void store_path(char out[PATH_MAX], NSString *path) {
    check(path.isAbsolutePath && strlen(path.fileSystemRepresentation) < PATH_MAX, @"Invalid user data path");
    strcpy(out, path.fileSystemRepresentation);
}
static NSString *file_hash(NSString *path) {
    int fd = open(path.fileSystemRepresentation, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    check(fd >= 0, [@"Cannot read migration input: " stringByAppendingString:path]);
    CC_SHA256_CTX hash; CC_SHA256_Init(&hash); unsigned char buffer[1 << 16], digest[32];
    ssize_t n;
    while ((n = read(fd, buffer, sizeof buffer)) > 0) CC_SHA256_Update(&hash, buffer, (CC_LONG)n);
    close(fd); check(n == 0, @"Failed reading migration input"); CC_SHA256_Final(digest, &hash);
    char hex[65]; for (unsigned i = 0; i < 32; i++) snprintf(hex + 2 * i, 3, "%02x", digest[i]);
    return @(hex);
}
/* Reject links/special files and compare every byte before publishing a cross-volume copy. */
static NSDictionary *inventory(NSString *root) {
    NSMutableDictionary *result = [NSMutableDictionary dictionary];
    NSDirectoryEnumerator *walk = [[NSFileManager defaultManager] enumeratorAtPath:root];
    check(walk != nil, @"Cannot enumerate legacy data");
    for (NSString *relative in walk) {
        NSString *path = child(root, relative); struct stat st;
        check(!lstat(path.fileSystemRepresentation, &st), @"Legacy data changed while being inspected");
        if (S_ISDIR(st.st_mode)) result[relative] = @"directory";
        else {
            check(S_ISREG(st.st_mode), [@"Migration refuses a link or special file: " stringByAppendingString:path]);
            result[relative] = @[@(st.st_size), file_hash(path)];
        }
    }
    return result;
}
static BOOL legacy_version(NSString *root, NSString *version) {
    NSString *marker = child(root, @"data-version.txt");
    if (exists(marker)) {
        NSString *text = [NSString stringWithContentsOfFile:marker encoding:NSUTF8StringEncoding error:nil];
        return [[text stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet] isEqual:version];
    }
    for (NSString *name in @[@"last-run.log", @"previous-run.log"]) {
        int fd = open(child(root, name).fileSystemRepresentation, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
        if (fd < 0) continue;
        char bytes[65537]; ssize_t n = read(fd, bytes, sizeof bytes - 1); close(fd);
        if (n <= 0) continue; bytes[n] = 0;
        char *found = strstr(bytes, "MNG_ACNH_VERSION:");
        if (found) {
            found += strlen("MNG_ACNH_VERSION:"); size_t size = strcspn(found, "\r\n \t");
            return size == strlen(version.UTF8String) && !strncmp(found, version.UTF8String, size);
        }
    }
    /* A packager-created empty profile has no save/version identity to import. */
    return NO;
}
static int take_lock(NSString *path, BOOL create) {
    int fd = open(path.fileSystemRepresentation, (create ? O_RDWR | O_CREAT : O_RDONLY) | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0 && !create && errno == ENOENT) return -1;
    check(fd >= 0, [@"Cannot open data lock: " stringByAppendingString:path]);
    if (flock(fd, LOCK_EX | LOCK_NB)) { close(fd); fail(@"Animal Crossing is running or another launch is migrating data. Quit the game and try again."); }
    return fd;
}
static void relocate(NSString *source, NSString *target) {
    if (!exists(source) || exists(target)) return;  /* Never overwrite existing user files. */
    NSError *error = nil;
    check([[NSFileManager defaultManager] moveItemAtPath:source toPath:target error:&error],
          [NSString stringWithFormat:@"Cannot relocate %@: %@", source, error.localizedDescription]);
}

int acnh_prepare_user_data(AcnhUserPaths *out, const char *user_home, const char *app_parent,
                          const char *raw_version, const char *override, char error[1024]) {
    @autoreleasepool {
        int setup_lock = -1, legacy_lock = -1;
        NSString *stage = nil;
        memset(out, 0, sizeof *out); error[0] = 0;
        @try {
            NSFileManager *fm = NSFileManager.defaultManager;
            NSString *version = @(raw_version);
            NSArray<NSString *> *parts = [version componentsSeparatedByString:@"."];
            check(parts.count == 3 && [parts[0] length] && [parts[1] length] && [parts[2] length]
                && [version rangeOfCharacterFromSet:
                [[NSCharacterSet characterSetWithCharactersInString:@"0123456789."] invertedSet]].location == NSNotFound,
                @"Invalid game data version");
            NSString *data, *cache, *logs;
            if (override && *override) {
                data = @(override); check(data.isAbsolutePath, @"ACNH_DATA_DIR must be an absolute directory path");
                directory(data); cache = child(data, @"shader-cache"); logs = data;
            } else {
                NSString *support_base, *cache_base, *logs_base;
                if (user_home) {
                    check([@(user_home) isAbsolutePath], @"Invalid user home");
                    support_base = child(@(user_home), @"Library/Application Support");
                    cache_base = child(@(user_home), @"Library/Caches");
                    logs_base = child(@(user_home), @"Library/Logs");
                } else {
                    support_base = [fm URLsForDirectory:NSApplicationSupportDirectory inDomains:NSUserDomainMask].firstObject.path;
                    cache_base = [fm URLsForDirectory:NSCachesDirectory inDomains:NSUserDomainMask].firstObject.path;
                    logs_base = child(NSHomeDirectory(), @"Library/Logs");
                }
                check(support_base && cache_base && logs_base, @"Cannot resolve macOS user directories");
                NSString *parent = child(support_base, bundle); directory(parent);
                setup_lock = take_lock(child(parent, [version stringByAppendingString:@".migration.lock"]), YES);
                data = child(parent, version);
                NSString *legacy = child(@(app_parent), @"Animal Crossing Data");
                if (!exists(data) && exists(legacy)) {
                    struct stat st;
                    check(!lstat(legacy.fileSystemRepresentation, &st) && S_ISDIR(st.st_mode), @"Legacy data must be a real directory");
                    /* Ignore an unused empty seed directory; refuse unidentifiable saves. */
                    BOOL has_save = [[fm contentsOfDirectoryAtPath:child(legacy, @"profile/save") error:nil] count] > 0;
                    BOOL identified = legacy_version(legacy, version);
                    check(identified || !has_save, @"Legacy save version is unknown or different. The original data was left untouched.");
                    if (identified) {
                        legacy_lock = take_lock(child(legacy, @"game-slot/lock"), NO);
                        NSDictionary *before = inventory(legacy);
                        if (renamex_np(legacy.fileSystemRepresentation, data.fileSystemRepresentation, RENAME_EXCL)) {
                            check(errno == EXDEV || errno == EACCES || errno == EPERM || errno == EROFS,
                                  @"Cannot move legacy data; original data was left untouched");
                            stage = child(parent, [NSString stringWithFormat:@".%@-migration-%@", version, NSUUID.UUID.UUIDString]);
                            NSError *copy_error = nil;
                            check([fm copyItemAtPath:legacy toPath:stage error:&copy_error], copy_error.localizedDescription ?: @"Legacy copy failed");
                            check([before isEqual:inventory(stage)] && [before isEqual:inventory(legacy)],
                                  @"Legacy data changed or its copy failed verification; original data was left untouched");
                            check(!renamex_np(stage.fileSystemRepresentation, data.fileSystemRepresentation, RENAME_EXCL),
                                  @"Cannot publish migrated data; original data was left untouched");
                            stage = nil; out->retained_legacy = 1;
                        }
                        out->migrated = 1;
                    }
                }
                directory(data);
                NSString *version_marker = child(data, @"data-version.txt");
                if (exists(version_marker)) check(legacy_version(data, version), @"Existing user data has a different game version");
                NSString *cache_root = child(child(cache_base, bundle), version); directory(cache_root);
                logs = child(child(logs_base, bundle), version); directory(logs);
                cache = child(cache_root, @"shader-cache");
                /* These moves are independently retryable after interruption. Save/settings never leave data. */
                relocate(child(data, @"shader-cache"), cache);
                for (NSString *name in [fm contentsOfDirectoryAtPath:data error:nil]) {
                    if ([name hasPrefix:@".romfs-verified"] || [name hasPrefix:@".dlc-verified"])
                        relocate(child(data, name), child(cache_root, name));
                }
                for (NSString *name in @[@"last-run.log", @"previous-run.log"])
                    relocate(child(data, name), child(logs, name));
                NSError *marker_error = nil;
                check([[version stringByAppendingString:@"\n"] writeToFile:version_marker
                    atomically:YES encoding:NSUTF8StringEncoding error:&marker_error], marker_error.localizedDescription ?: @"Cannot record data version");
            }
            directory(cache); directory(logs);
            store_path(out->data, data); store_path(out->cache, cache); store_path(out->logs, logs);
            if (legacy_lock >= 0) close(legacy_lock);
            if (setup_lock >= 0) close(setup_lock);
            return 0;
        } @catch (NSException *exception) {
            snprintf(error, 1024, "%s", exception.reason.UTF8String);
            if (stage) [[NSFileManager defaultManager] removeItemAtPath:stage error:nil];
            if (legacy_lock >= 0) close(legacy_lock);
            if (setup_lock >= 0) close(setup_lock);
            return 1;
        }
    }
}
