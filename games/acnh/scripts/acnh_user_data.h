/* User-domain paths and one-time migration of the old App-adjacent directory. */
#pragma once
#include <limits.h>

typedef struct {
    char data[PATH_MAX], cache[PATH_MAX], logs[PATH_MAX];
    int migrated, retained_legacy;
} AcnhUserPaths;

/* user_home is NULL in the launcher (Foundation resolves user directories).
 * Tests pass an isolated home directory directly, without changing HOME.
 * An explicit ACNH_DATA_DIR keeps the original self-contained layout and skips migration. */
int acnh_prepare_user_data(AcnhUserPaths *out, const char *user_home,
                          const char *app_parent, const char *version,
                          const char *override, char error[1024]);
