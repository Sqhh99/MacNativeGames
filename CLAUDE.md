# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Repository policy (branches, PR targets, commit identity, local asset and build layout) is in AGENTS.md and applies in full:

@AGENTS.md

## Mandatory records

Follow `agents/skills/project-records/SKILL.md` (read it before writing one):
- after any request that changes files, a work log in `docs/work-logs/YYYY-MM-DD-<topic>.md`;
- after any code review, a review archive in `docs/code-reviews/`;
- before opening a pull request, a PR record in `docs/pull-requests/`, used as the PR body.

Never tick a verification box for a command that was not run.

## What this is

Native ports of Nintendo Switch games to Apple silicon. This is **not an emulator**: the game's own ARM64 code is rewritten ahead of time
(only what macOS forbids: x18, the thread-pointer register, `svc`, counter registers), loaded at its original layout, and runs directly.
A small host answers Horizon system calls and IPC (HLE), and NVN graphics are replayed on Metal 4. Everything game-specific is made
at build time from the player's own XCI/NSP and `prod.keys`; the repository holds no game content.

## Commands

Python 3.14 is required (the tests and build use the standard-library `compression.zstd`).

```sh
python3.14 -m pip install -r games/totk/requirements.txt   # once; the test suite needs these
make check                                                  # Python tests + three of the native UBSan tests
python3.14 -m unittest discover -s tests -v                 # what CI runs
python3.14 -m unittest tests.test_work_directory            # one module (run from the repo root; tests import build_app)
python3.14 -m unittest tests.test_work_directory.WorkDirectoryTests.test_existing_tooling_link_is_detached_before_child_links_change
```

CI (`.github/workflows/tests.yml`) also compiles and runs these C tests with `-std=c11 -Wall -Wextra -Werror -fsanitize=undefined
-fno-sanitize-recover=all` (UBSan only; ASan hangs in dyld on macOS 26): `test_romfs_paths.c`, `test_feedback_settings.c`,
`test_controller_map.c`, `test_keyboard_map.c`, `test_game_language.c`, `test_audio_ramp.c`, `test_bow_state.c`. `make check` covers the
romfs-path, controller-map and keyboard-map ones.

Building an app (20–40 min, must not be interrupted; rerunning the same command resumes from the work folder):

```sh
python3.14 build_app.py "<base.xci|nsp>" -k "<prod.keys>" [--update <nsp|nsz>] [--dlc <nsp> ...] \
  [--firmware <nca dir> | --shared-fonts <dir>] [--platform macos|ios|visionos] --work <dir> -o <app|ipa>
python3.14 update_runtime.py "<app>" [--work <dir>] [--seed]   # swap in a new runtime without game files (~1 min)
```

Per AGENTS.md, local builds always pass explicit `--work build/<game>-<version>/work` and `-o build/<game>-<version>/...`;
`build/build_game.py` and `build/package_game.py` are the owner's (git-ignored) wrappers for the selected versions.
The player-facing procedure and error table is `.claude/skills/install-zelda/SKILL.md`.

Developer targets live in `games/totk/Makefile` (run from `games/totk`, uses `.venv/bin/python`; `make dependencies` creates it):
`runtime-<version>` / `binary-<version>` / `game-data-<version>` (versions `v112 v121 v143 botw160 botw190`; 1.0.0 is plain
`runtime` / `binary` / `game-data-v0`) and many
`probe-*` targets. GPU probes serialize through `scripts/dev/game_slot.py` (one game or GPU probe at a time; `TOTK_SLOT_OWNER` names the waiter).

## Architecture

**`games/totk` is shared by Tears of the Kingdom and Breath of the Wild** (one runtime with per-game switches; BotW-only assets and
scripts are in `games/botw`). Every other game (`ssbu`, `odyssey`, `by3`, `wonder`, `ori`, `jamboree`, `mvdk`, `dread`) is a
self-contained community port with its own runtime, graphics layer, rewriter, prebuilt translator and Makefile. Its build must
never read or import another game's folder; copies are recorded (e.g. `third_party/COPIES.md`). A change for one game never edits another's files.

Within `games/totk`:
- `third_party/d2r/patch_nso.py` — the ahead-of-time NSO rewriter (from d2r-mobile). Output is bound by SHA-256 and checked
  against `assets/expected-v<version>.json`.
- `runtime/` — the host: `loader.c` maps main/sdk/subsdk0 and starts `nn::init::Start`; `services.c`, `ipc.c`, `threads.c`, `fs_host.c`,
  `romfs.c`, audio, input, `frontend.m` (macOS) / `frontend_ios.m`. `game_patches*.c` holds the few fixed game patches (60 FPS,
  resolution, timing); each verifies the original instruction before writing. `game_version.h` pins per-version addresses.
  `game_data.h` describes the per-build game data folder (module tables, RomFS/font hashes) the binary reads at every start,
  so the compiled binary contains nothing from the game and can be replaced by `update_runtime.py`.
- `third_party/d2r_gfx/gfx/nvn` — NVN implemented on Metal: memory pools → Metal resources with dirty-page tracking, command
  buffers replayed as render passes/draws. It maps NVN semantics only; game-specific handling sits apart behind a switch.
- Shaders: Maxwell code → Ryujinx translator (`vendor/ryujinx`, shipped as the NativeAOT binary `prebuilt/macos-arm64/totk_xlate`,
  rebuilt with `tools/totk_xlate/publish_native.sh` and .NET 10) → SPIR-V → SPIRV-Cross (fetched at a pinned commit) → MSL → Metal.
  The shared shader list (`assets/shader_list.tsv`, `games/botw/assets/shader_list.tsv`) holds identifiers only; `scripts/shader_list.py`
  exports warm-up manifests.
- Input on the Mac: window keys and mouse buttons go through the player's layout (`runtime/keyboard_map.h`, `keyboard.txt`),
  controllers through `runtime/controller_map.h` (`controls.txt`); the settings panel (key 1, `runtime/settings_panel.h`)
  edits both. Scripted input (`TOTK_INPUT_SCRIPT`, `TOTK_INPUT_FILE`, auto-load) keeps a fixed layout in `runtime/input.c`.
  Host text is English, Chinese or Japanese (`totk_ui_lang.h`: `TOTK_UI` with the `totk_ui_ja` table, or `TOTK_UI3`).
- `ios/` — XcodeGen project (`project.yml`; BotW-only files are excluded there) and IPA/device tools.

`build_app.py` (root) drives four checked stages: (1) code — ExeFS from XCI/NSP, optional `--mod` main patches merged
(`scripts/mod_exefs.py`, refused on sites in `scripts/patch_sites.py`), then rewritten; (2) data — RomFS verified through all IVFC
levels, shared fonts, RomFS overlays; (3) shaders — startup seed translated from the RomFS; (4) game binary + game data folder +
app bundle/IPA, then a `--check` start. Every intermediate goes in the work folder and is reused only if its recorded inputs and hashes still match.

`docs/how-it-works.md` has the full design; per-version port notes are `docs/v1.2.1-port.md`, `docs/v1.4.3-port.md`, `docs/botw-v1.9.0-port.md`.

## Rules from CONTRIBUTING.md

- No CPU emulation of any kind (interpreter, JIT, DBT, Unicorn/QEMU, emulator CPU backends) and no copying Horizon services/IPC
  from emulators. Emulators may only be used as an outside reference.
- Fix platform bugs in the platform layer, not with another game-code patch. Keep game-logic changes minimal and optional.
- The game is always rebuilt from unmodified original files; never patch a rewritten binary or hand-edit bytes. Never weaken or
  edit `expected-*.json` / `game_version.h` to get past a hash error.
- Picture correctness before speed. Mac: no loss of picture quality. iOS: slight loss allowed, never lower resolution, behind an
  iOS condition. Decide optimizations from measurement (Instruments, Metal HUD, the repo's diagnostic switches).
- Diagnostics and unfinished experiments are off by default, enabled by environment variable or input-file command.
- Code shared with iOS (the runtime, `d2r_gfx`) must also build with `build_app.py --platform ios`.
- No GPL code or code from other mods. Never commit game files, keys, saves, or translated shaders.
- Commit messages: `<type>: <description>`, type one of feat, fix, refactor, docs, test, chore, perf, ci.
