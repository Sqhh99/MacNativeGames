"""Exercise native user-directory migration without touching the real Library or saves."""
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

GAME = Path(__file__).resolve().parents[1]
BUNDLE = "com.nintendo.acnh.native"


class UserDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        root = Path(cls.build.name)
        probe = root / "probe.c"
        probe.write_text(r'''
#include "acnh_user_data.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#undef renamex_np
int renamex_np(const char *, const char *, unsigned int);
int fixture_renamex_np(const char *source, const char *target, unsigned int flags) {
    if (getenv("ACNH_TEST_CROSS_VOLUME") && strstr(source,"/Animal Crossing Data")) { errno=EXDEV; return -1; }
    if (getenv("ACNH_TEST_PUBLISH_FAILURE") && strstr(source,"-migration-")) { errno=EACCES; return -1; }
    return renamex_np(source,target,flags);
}
int main(int argc,char **argv) {
    if(argc!=4&&argc!=5)return 2;
    AcnhUserPaths paths; char error[1024];
    if(acnh_prepare_user_data(&paths,argv[1],argv[2],argv[3],argc==5?argv[4]:NULL,error)) {
        fprintf(stderr,"%s\n",error); return 1;
    }
    printf("%s\n%s\n%s\n%d %d\n",paths.data,paths.cache,paths.logs,paths.migrated,paths.retained_legacy);
    return 0;
}
''')
        cls.binary = root / "probe"
        result = subprocess.run(["xcrun", "clang", "-O2", "-Wall", "-Wextra", "-Werror",
            "-Wno-deprecated-declarations", "-fobjc-arc", "-Drenamex_np=fixture_renamex_np",
            "-I", str(GAME / "scripts"), str(probe), str(GAME / "scripts/acnh_user_data.m"),
            "-framework", "Foundation", "-o", str(cls.binary)], capture_output=True, text=True)
        if result.returncode:
            cls.build.cleanup()
            raise RuntimeError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "user"
        self.apps = self.root / "Applications"
        self.apps.mkdir()
        self.legacy = self.apps / "Animal Crossing Data"
        self.data = self.home / "Library/Application Support" / BUNDLE / "3.0.1"
        self.cache = self.home / "Library/Caches" / BUNDLE / "3.0.1/shader-cache"
        self.logs = self.home / "Library/Logs" / BUNDLE / "3.0.1"

    def run_probe(self, *, expected=0, override=None, extra_env=None, version="3.0.1"):
        args = [str(self.binary), str(self.home), str(self.apps), version]
        if override is not None:
            args.append(str(override))
        env = dict(os.environ)
        env.pop("ACNH_TEST_CROSS_VOLUME", None)
        env.pop("ACNH_TEST_PUBLISH_FAILURE", None)
        env.update(extra_env or {})
        result = subprocess.run(args, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def legacy_fixture(self, version="3.0.1"):
        files = {
            "profile/save/local/main.dat": b"island save\x00\xff",
            "profile/save/local/player.dat": b"player save",
            "profile/account.uid": b"account-identity",
            "backups/older/main.dat": b"earlier save",
            "frame-rate.txt": b"60\n", "language.txt": b"ja\n",
            "keyboard.txt": b"custom key bindings\n", "controls.txt": b"controller choice\n",
            "Screenshots/example.png": b"synthetic screenshot",
            "shader-cache/compiled/one.bin": b"compiled shader",
            ".romfs-verified-v1": b"verification proof", ".dlc-verified-title-v1": b"DLC proof",
            "last-run.log": f"startup\n[acnh] MNG_ACNH_VERSION:{version}\n".encode(),
            "previous-run.log": b"previous log", "game-slot/lock": b"",
        }
        for name, data in files.items():
            path = self.legacy / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return files

    def test_fresh_launch_uses_library_without_writing_beside_the_app(self):
        self.apps.chmod(0o555)
        self.addCleanup(self.apps.chmod, 0o755)
        result = self.run_probe()
        self.assertEqual(result.stdout.splitlines(), [str(self.data), str(self.cache), str(self.logs), "0 0"])
        self.assertFalse(self.legacy.exists())
        self.assertEqual((self.data / "data-version.txt").read_text(), "3.0.1\n")
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o700)

    def test_migration_preserves_saves_preferences_backups_and_separates_cache_logs(self):
        files = self.legacy_fixture()
        result = self.run_probe()
        self.assertEqual(result.stdout.splitlines()[-1], "1 0")
        self.assertFalse(self.legacy.exists())
        for name, content in files.items():
            if name.startswith("shader-cache/"):
                actual = self.cache / name[len("shader-cache/"):]
            elif name.startswith((".romfs-verified", ".dlc-verified")):
                actual = self.cache.parent / name
            elif name in ("last-run.log", "previous-run.log"):
                actual = self.logs / name
            else:
                actual = self.data / name
            self.assertEqual(actual.read_bytes(), content, name)
        self.run_probe()
        self.assertEqual((self.data / "profile/save/local/main.dat").read_bytes(), files["profile/save/local/main.dat"])

    def test_existing_destination_never_merges_or_overwrites_another_save(self):
        self.run_probe()
        save = self.data / "profile/save/local/main.dat"
        save.parent.mkdir(parents=True); save.write_bytes(b"new authoritative progress")
        self.legacy_fixture()
        self.run_probe()
        self.assertEqual(save.read_bytes(), b"new authoritative progress")
        self.assertTrue(self.legacy.is_dir())

    def test_busy_legacy_game_blocks_migration_until_it_exits(self):
        self.legacy_fixture()
        with (self.legacy / "game-slot/lock").open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_probe(expected=1)
            self.assertIn("Quit the game", result.stderr)
            self.assertTrue(self.legacy.is_dir()); self.assertFalse(self.data.exists())
        self.run_probe()

    def test_unknown_or_different_version_never_imports_a_save(self):
        self.legacy_fixture("1.2.1")
        self.assertIn("version is unknown or different", self.run_probe(expected=1).stderr)
        self.assertFalse(self.data.exists()); self.assertTrue(self.legacy.is_dir())
        self.run_probe(version="1.2.1")
        self.assertTrue((self.data.parent / "1.2.1/profile/save/local/main.dat").exists())
        self.assertFalse(self.data.exists())

    def test_links_in_legacy_data_are_rejected_without_touching_the_target(self):
        self.legacy_fixture()
        outside = self.root / "outside"
        outside.write_bytes(b"leave this alone")
        (self.legacy / "linked-save").symlink_to(outside)
        self.assertIn("refuses a link", self.run_probe(expected=1).stderr)
        self.assertEqual(outside.read_bytes(), b"leave this alone")
        self.assertTrue(self.legacy.is_dir()); self.assertFalse(self.data.exists())

    def test_explicit_override_keeps_isolated_layout_and_skips_legacy_migration(self):
        self.legacy_fixture()
        override = self.root / "test-data"
        result = self.run_probe(override=override)
        self.assertEqual(result.stdout.splitlines(), [str(override), str(override / "shader-cache"), str(override), "0 0"])
        self.assertTrue(self.legacy.is_dir()); self.assertFalse(self.home.exists())
        self.assertIn("absolute directory", self.run_probe(override="relative-path", expected=1).stderr)

    def test_cross_volume_copy_is_verified_and_keeps_original_data(self):
        files = self.legacy_fixture()
        result = self.run_probe(extra_env={"ACNH_TEST_CROSS_VOLUME": "1"})
        self.assertEqual(result.stdout.splitlines()[-1], "1 1")
        for name in ("profile/save/local/main.dat", "frame-rate.txt", "profile/account.uid"):
            self.assertEqual((self.data / name).read_bytes(), files[name])
            self.assertEqual((self.legacy / name).read_bytes(), files[name])

    def test_failed_publish_keeps_legacy_data_and_can_be_retried(self):
        self.legacy_fixture()
        self.run_probe(expected=1, extra_env={"ACNH_TEST_CROSS_VOLUME": "1", "ACNH_TEST_PUBLISH_FAILURE": "1"})
        self.assertFalse(self.data.exists()); self.assertTrue(self.legacy.is_dir())
        self.assertFalse(list(self.data.parent.glob(".*-migration-*")))
        self.run_probe()

    def test_invalid_versions_cannot_escape_the_user_directory(self):
        for version in ("..", ".", "1.2", "1..3", "1.2.3/other", "1.2.3.4"):
            self.assertIn("Invalid game data version", self.run_probe(version=version, expected=1).stderr)
        self.assertFalse(self.home.exists())

    def test_mismatched_destination_marker_is_never_rewritten(self):
        self.run_probe()
        marker = self.data / "data-version.txt"
        marker.write_text("1.2.1\n")
        self.assertIn("different game version", self.run_probe(expected=1).stderr)
        self.assertEqual(marker.read_text(), "1.2.1\n")


if __name__ == "__main__":
    unittest.main()
