/* Language of the host's own text on screen (boot screen, warm-up progress, overlays, the settings panel, keyboard prompt):
   English, Chinese or Japanese. On the Mac it is English until the player picks another in the settings panel (key 1;
   user 2026-10-27: English by default, whatever the Mac's language), kept in ui-language.txt next to controls.txt, which
   runtime/frontend.m and app/launcher.m read at start into totk_ui_choice. The iPhone and iPad have no settings panel and
   follow the first of the user's preferred languages. TOTK_UI_LANG=en, zh or ja decides over both (read on every call, so
   tests can switch). The game's own language is chosen separately (TOTK_LANG, services.c desired_language).
   TOTK_UI(zh, en) gives the Japanese of en from totk_ui_ja below (English where it has none); TOTK_UI3(zh, en, ja) names
   all three. */
#pragma once
#include <CoreFoundation/CoreFoundation.h>
#include <TargetConditionals.h>
#include <stdlib.h>
#include <string.h>

enum { TOTK_UI_EN, TOTK_UI_ZH, TOTK_UI_JA, TOTK_UI_LANGUAGES };

/* The settings panel's pick, -1 none. One variable for the whole program: a weak definition, which the linker merges into
   one however many files include this header. */
__attribute__((weak)) int totk_ui_choice = -1;

/* The language a word names ("en", "zh", "ja", also "zh-Hans", "ja_JP"; white space around it ignored), or -1. */
static inline int totk_ui_lang_parse(const char *s) {
    if (!s) return -1;
    while (*s == ' ' || *s == '\t' || *s == '\r' || *s == '\n') s++;
    if (!strncmp(s, "en", 2)) return TOTK_UI_EN;
    if (!strncmp(s, "zh", 2)) return TOTK_UI_ZH;
    if (!strncmp(s, "ja", 2)) return TOTK_UI_JA;
    return -1;
}
static inline const char *totk_ui_lang_name(int language) {
    return language == TOTK_UI_ZH ? "zh" : language == TOTK_UI_JA ? "ja" : "en";
}

static inline int totk_ui_language(void) {
    const char *e = getenv("TOTK_UI_LANG");
    if (e && *e) { int l = totk_ui_lang_parse(e); return l < 0 ? TOTK_UI_EN : l; }
    int choice = __atomic_load_n(&totk_ui_choice, __ATOMIC_RELAXED);
    if (choice >= 0 && choice < TOTK_UI_LANGUAGES) return choice;
#if TARGET_OS_IPHONE
    static int system = -1;
    if (system < 0) {
        char language[16] = {0};
        CFArrayRef preferred = CFLocaleCopyPreferredLanguages();
        if (preferred && CFArrayGetCount(preferred) > 0)
            CFStringGetCString((CFStringRef)CFArrayGetValueAtIndex(preferred, 0), language, sizeof language, kCFStringEncodingUTF8);
        if (preferred) CFRelease(preferred);
        int l = totk_ui_lang_parse(language);
        system = l < 0 ? TOTK_UI_EN : l;
    }
    return system;
#else
    return TOTK_UI_EN;
#endif
}
static inline int totk_ui_zh(void) { return totk_ui_language() == TOTK_UI_ZH; }

/* Japanese for the English text of TOTK_UI (the boot screen, the warm-up, the overlay, the launcher's dialogs); the English
   itself when it is not listed. tests/test_ui_language.py checks that every TOTK_UI text of those files is here. */
static inline const char *totk_ui_ja(const char *en) {
    static const char *const table[][2] = {
        {"Starting", "起動しています"},
        {"Working, please wait", "処理しています。しばらくお待ちください"},
        {"Warming shaders and pipelines %.0f%%", "シェーダーとパイプラインを準備しています %.0f%%"},
        {"shaders %llu/%llu · pipelines %llu/%llu", "シェーダー %llu/%llu · パイプライン %llu/%llu"},
        {"%llu/%llu items", "%llu/%llu 件"},
        {"Live frame rate (TOTK_MENUBAR_FPS=0 hides it)", "現在のフレームレート（TOTK_MENUBAR_FPS=0 で非表示）"},
        {"Build %s", "ビルド %s"},
        {"Test session (%s) Ver. %s: %s — save copy, progress is not saved to your save, the script closes it",
         "テストセッション（%s）Ver. %s：%s — セーブのコピーで動作中。進行状況は保存されず、スクリプトが終了します"},
        {"agent test", "エージェントのテスト"},
        {"Starting Hyrule", "ハイラルを起動しています"},
        {"Preparing the game environment", "ゲーム環境を準備しています"},
        {"Running the %s game module initializers (%u/%u)", "%s ゲームモジュールの初期化コードを実行しています（%u/%u）"},
        {"Initializing game modules", "ゲームモジュールを初期化しています"},
        {"Starting the game runtime", "ゲームのランタイムを起動しています"},
        {"Connecting the game code to macOS system services", "ゲームのコードを macOS のシステムサービスに接続しています"},
        {"Game data verification record is valid", "ゲームデータの検証記録は有効です"},
        {"Verifying game data", "ゲームデータを検証しています"},
        {"Reading the data index", "データのインデックスを読み込んでいます"},
        {"Preparing game data", "ゲームデータを準備しています"},
        {"Checking the resolution patch and mounting the read-only game data", "解像度パッチを確認し、読み取り専用のゲームデータをマウントしています"},
        {"Verifying add-on content", "追加コンテンツを検証しています"},
        {"Enter text", "文字を入力"},
        {"  MetalFX on", "  MetalFX オン"},
        {"Missing shaders %llu / total %s", "不足シェーダー %llu / 合計 %s"},
        {"New shaders %llu / total %s", "新しいシェーダー %llu / 合計 %s"},
        {"New render pipelines %llu / total %s", "新しいレンダーパイプライン %llu / 合計 %s"},
        {"Creating the Metal device", "Metal デバイスを作成しています"},
        {"Preparing the GPU, command queues and graphics resources", "GPU、コマンドキュー、グラフィックスリソースを準備しています"},
        {"Preparing the shader cache", "シェーダーキャッシュを準備しています"},
        {"Checking the local cache and reading the shader lists", "ローカルキャッシュを確認し、シェーダーリストを読み込んでいます"},
        {"Importing the app's shaders", "アプリのシェーダーを取り込んでいます"},
        {"Verifying the app's shaders", "アプリのシェーダーを検証しています"},
        {"Checking the shader cache", "シェーダーキャッシュを確認しています"},
        {"Verifying the shaders bundled with the app and importing them into the local cache if needed",
         "アプリ付属のシェーダーを検証し、必要に応じてローカルキャッシュに取り込んでいます"},
        {"Shader cache not ready", "シェーダーキャッシュを準備できませんでした"},
        {"Could not import the shaders bundled with the app; shaders are translated during play",
         "アプリ付属のシェーダーを取り込めませんでした。プレイ中にシェーダーを変換します"},
        {"Shader cache ready", "シェーダーキャッシュの準備ができました"},
        {"Imported %llu prepared files; starting warm-up", "準備済みファイルを %llu 個取り込みました。ウォームアップを開始します"},
        {"Reading the shaders bundled with the app in place, nothing to import; starting warm-up",
         "アプリ付属のシェーダーをそのまま読み込みます（取り込み不要）。ウォームアップを開始します"},
        {"Local cache already present, nothing to import; starting warm-up", "ローカルキャッシュがあるため取り込みは不要です。ウォームアップを開始します"},
        {"No bundled shader seed; continuing graphics setup", "付属のシェーダーシードがありません。グラフィックスの準備を続けます"},
        {"We would love your contribution", "ぜひご協力ください"},
        {"You have %lu shaders and render pipelines to contribute: ones your game met that the shared shader list does not have yet. "
         "They are kept in a small file with shader and pipeline identifiers only: no game data, saves or personal information. "
         "Sent to GitHub and added to the shared list, they come with everyone's next build, and nobody stutters there again.\n\n",
         "提供できるシェーダーとレンダーパイプラインが %lu 件あります。プレイ中に出会い、共有シェーダーリストにまだないものです。"
         "小さなファイルにシェーダーとパイプラインの識別子だけが記録されており、ゲームデータ、セーブ、個人情報は含まれません。"
         "GitHub に送って共有リストに加えると、次からみんなのビルドに含まれ、その場面でカクつくことがなくなります。\n\n"},
        {"\"Submit automatically\" sends it now with the GitHub CLI (gh) signed in on this Mac, without the browser. "
         "\"Send\" opens the GitHub form and shows the file in Finder: drag it into the form.",
         "「自動で送信」は、この Mac でサインイン済みの GitHub CLI（gh）を使い、ブラウザを開かずに送信します。"
         "「送信」は GitHub のフォームを開き、Finder でファイルを表示します。ファイルをフォームにドラッグしてください。"},
        {"\"Send\" opens the GitHub form and shows the file in Finder: drag it into the form.",
         "「送信」は GitHub のフォームを開き、Finder でファイルを表示します。ファイルをフォームにドラッグしてください。"},
        {"Send", "送信"},
        {"Submit automatically", "自動で送信"},
        {"Remind me next time", "次回また通知"},
        {"Don't remind me again", "今後は通知しない"},
        {"⭐ Like it? Star it on GitHub", "⭐ 気に入ったら GitHub でスターを"},
        {"Thank you for your shader contribution! Let's make the game smoother together!",
         "シェーダーの提供ありがとうございます！一緒にゲームをもっと快適にしましょう！"},
        {"Submitting automatically did not work; opening the form instead.", "自動送信できなかったため、代わりにフォームを開きます。"},
    };
    for (size_t i = 0; i < sizeof table / sizeof *table; i++) if (!strcmp(table[i][0], en)) return table[i][1];
    return en;
}

static inline const char *totk_ui_pick(const char *zh, const char *en, const char *ja) {
    int language = totk_ui_language();
    return language == TOTK_UI_ZH ? zh : language == TOTK_UI_JA ? (ja ? ja : totk_ui_ja(en)) : en;
}
#define TOTK_UI(zh, en) totk_ui_pick((zh), (en), NULL)
#define TOTK_UI3(zh, en, ja) totk_ui_pick((zh), (en), (ja))
