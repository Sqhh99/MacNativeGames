"""Packaged-app migration rejects malformed file indexes and Mach-O metadata."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import build_app
import update_runtime
from import_app_data import LegacyMachO, import_app, romfs_manifest


def index(rows):
    strings, entries = bytearray(), bytearray()
    for name, offset, size in rows:
        name = name.encode() + b'\0'
        entries.extend(struct.pack('<QQII', offset, size, len(strings), len(name)))
        strings.extend(name)
    return struct.pack('<8sQQ', b'TOTKRFS1', len(rows), 24 + len(entries)) + entries + strings


class RomfsImport(unittest.TestCase):
    def test_recovers_packaged_paths_for_shader_scanning(self):
        data = index([('Pack/Bootup.pack', 16, 32), ('System/Shader.ssarc', 48, 16)])
        result = romfs_manifest(data, 64, 'a' * 64)
        self.assertEqual(result['files'], [dict(path='Pack/Bootup.pack', offset=16, size=32),
                                           dict(path='System/Shader.ssarc', offset=48, size=16)])
        self.assertEqual(result['romfs_sha256'], 'a' * 64)

    def test_rejects_truncation_and_entry_outside_image(self):
        valid = index([('Pack/Bootup.pack', 16, 32)])
        for bad in (valid[:8], b'INVALID!' + valid[8:], valid[:-1], index([('Pack/Bootup.pack', 48, 32)])):
            with self.subTest(data=bad), self.assertRaises(build_app.BuildError):
                romfs_manifest(bad, 64, 'a' * 64)

    def test_rejects_duplicate_and_noncanonical_paths(self):
        for paths in (['a', 'a'], ['../a'], ['/a'], ['a/../b'], ['a//b'], ['a\0b']):
            with self.subTest(paths=paths), self.assertRaises(build_app.BuildError):
                romfs_manifest(index([(name, 0, 1) for name in paths]), 64, 'a' * 64)


class LegacyMachOImport(unittest.TestCase):
    def test_unpinned_game_modules_are_rejected_before_any_import(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            module = root / 'Game.app/Contents/Resources/totk/rewritten/botw160/main.patched.bin'
            module.parent.mkdir(parents=True)
            module.write_bytes(b'a different game module')
            with self.assertRaisesRegex(build_app.BuildError, 'repository-pinned rewrite'):
                import_app(root / 'Game.app', root / 'work', 'botw160', build_app.VERSIONS['botw160'])
            self.assertFalse((root / 'work').exists())

    def fixture(self):
        vm = 0x100000000
        data = bytearray(1024)
        struct.pack_into('<8I', data, 0, 0xfeedfacf, 0x100000c, 0, 2, 2, 96, 0, 0)
        struct.pack_into('<II16s4Q4I', data, 32, 0x19, 72, b'__TEXT', vm, 1024, 0, 1024, 7, 5, 0, 0)
        struct.pack_into('<6I', data, 104, 2, 24, 700, 1, 768, 10)
        struct.pack_into('<IBBHQ', data, 700, 1, 0x0f, 1, 0, vm + 256)
        data[768:778] = b'\0_modules\0'
        struct.pack_into('<Q', data, 256, 0x005000000000012c)  # a chained pointer, not an absolute address
        data[300:306] = b'hello\0'
        return data

    def test_resolves_chained_pointer_without_executing_old_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'old-native'
            path.write_bytes(self.fixture())
            fixups = '  __DATA __data 0x100000100 rebase 0x10000012C\n'
            with mock.patch('import_app_data.subprocess.run', return_value=mock.Mock(returncode=0, stdout=fixups)) as run:
                image = LegacyMachO(path)
            self.assertEqual(image.symbols['_modules'], 0x100000100)
            self.assertEqual(image.string(image.pointer(0x100000100)), 'hello')
            self.assertEqual(run.call_args.args[0][:3], ['xcrun', 'dyld_info', '-fixups'])
            with self.assertRaises(build_app.BuildError):
                image.read(0x1000003ff, 2)

    def test_rejects_malformed_segment_before_invoking_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'old-native'
            data = self.fixture()
            struct.pack_into('<Q', data, 32 + 48, 2048)  # filesize exceeds the actual file
            path.write_bytes(data)
            with mock.patch('import_app_data.subprocess.run') as run, self.assertRaises(build_app.BuildError):
                LegacyMachO(path)
            run.assert_not_called()

    def test_imported_data_is_available_without_original_build_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            tree, res = Path(folder) / 'work', Path(folder) / 'app'
            imported = tree / 'build/game-data/botw160'
            imported.mkdir(parents=True)
            for name in build_app.game_data_files('botw160'):
                (imported / name).write_text('fixture')
            with mock.patch.object(update_runtime, 'run') as run:
                self.assertEqual(update_runtime.game_data(tree, res, 'botw160', tree / 'logs', {}), imported)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
