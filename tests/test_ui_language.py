"""The host's own text in Japanese (games/totk/third_party/d2r_gfx/gfx/nvn/include/totk_ui_lang.h): every TOTK_UI text of
the boot screen, the warm-up, the overlay and the launcher's dialogs has its Japanese in totk_ui_ja, so picking 日本語 in
the settings panel leaves no English behind there. Texts named with TOTK_UI3 carry their Japanese themselves."""
import re
import unittest
from pathlib import Path

TOTK = Path(__file__).resolve().parents[1] / 'games/totk'
HEADER = TOTK / 'third_party/d2r_gfx/gfx/nvn/include/totk_ui_lang.h'
SOURCES = ['runtime/frontend.m', 'runtime/frontend_ios.m', 'runtime/loader.c', 'runtime/romfs.c', 'runtime/aoc_romfs.c',
           'runtime/swkbd_host.c', 'runtime/playtime.h', 'app/launcher.m', 'app/update_notice.h', 'third_party/d2r_gfx/gfx/nvn/fps_overlay.c',
           'third_party/d2r_gfx/gfx/nvn/nvn_mtl.m', 'third_party/d2r_gfx/gfx/nvn/totk_shader_rt.m']
LITERAL = r'"(?:[^"\\]|\\.)*"'
STRING = r'((?:' + LITERAL + r'\s*)+)'


def joined(text):
    """The contents of adjacent C string literals, as written (escapes kept)."""
    return ''.join(literal[1:-1] for literal in re.findall(LITERAL, text))


class UILanguageTests(unittest.TestCase):
    def test_every_text_has_japanese(self):
        header = HEADER.read_text()
        body = header[header.index('totk_ui_ja(const char *en)'):header.index('static inline const char *totk_ui_pick')]
        table = {joined(en): joined(ja) for en, ja in re.findall(r'\{\s*' + STRING + r',\s*' + STRING + r'\}', body)}
        self.assertGreater(len(table), 40)
        missing = []
        for source in SOURCES:
            text = (TOTK / source).read_text()
            for match in re.finditer(r'TOTK_UI\(\s*' + STRING + r',\s*' + STRING + r'\)', text):
                english = joined(match.group(2))
                if english not in table:
                    missing.append(f'{source}: {english}')
        self.assertEqual(missing, [], 'TOTK_UI texts without Japanese in totk_ui_ja (or use TOTK_UI3)')
        for english, japanese in table.items():
            self.assertEqual(sorted(re.findall(r'%[0-9.]*l*[a-z%@]', english)), sorted(re.findall(r'%[0-9.]*l*[a-z%@]', japanese)),
                             f'format arguments differ: {english}')


if __name__ == '__main__':
    unittest.main()
