# Work log: merge the local `main` snapshot into `sqhh99`

- **Date:** 2026-10-27
- **Branch:** `sqhh99` (at `74b25d7`), merging local `main` at `8c9c71b`
- **Related:** follows [2026-10-27-input-remap-settings.md](2026-10-27-input-remap-settings.md)

## 1. Request
> I have synced the code from the `main` branch of my forked repository, and my local `main` branch now includes these updates. Could you please merge the code from the `main` branch into the `sqhh99` branch?

Merge the owner's refreshed local `main` into `sqhh99` and keep the owner's changes. Per AGENTS.md, use the local `main` as it is and do not fetch from upstream.

## 2. Plan
1. Merge local `main` (64 commits since the merge base `bb1940f`) into `sqhh99` without committing. Nothing was fetched.
2. Resolve the conflicts so that both sides' changes are kept.
3. Check the files both sides changed (`gamepad.m`, `input.c`, `runtime.h`, `input_probe.c`) and the probes that compile them.
4. Run the tests, then commit the merge.

What main brings: new community ports `games/acnh`, `games/eow` and `games/unicorn`. TOTK/BotW changes:
- HID rumble from a table of controller profiles (`rumble-profiles.txt`);
- 8BitDo Ultimate 2 gyro read from HID;
- Switch Pro right stick read from HID;
- Joy-Con motion;
- the `mscan` memory-scan diagnostics;
- the `TOTK_INPUT_FILE` reopen;
- motion states on the 5 ms console clock;
- emulator save import/export (`save_manager.py`);
- the benchmark route;
- iOS install and seed checks;
- `TOTK_PCHTXT` in the app.

## 3. Files changed
| File | Change | Addresses |
|---|---|---|
| `docs/controls.md`, `docs/controls.zh-CN.md` | Conflict resolved. Main's longer controller paragraph, with the HID rumble profiles, is kept. Its closing lead-in to the old keyboard table ("Mac keyboard mappings use…" / "Mac 键盘映射按…") is dropped, because `sqhh99` replaced that table with the keyboard-and-mouse section that follows. | Both sides' text kept |
| `games/totk/scripts/input_file_probe.c` | Adds a `runtime_setting_remove` stub. `runtime_keymap_reset` in `input.c` (from `b33bf3a`) calls it, so `make probe-input-file` stopped linking. The gap is from our remap commit, not from main. | Probe builds again |
| Everything else from `main` | Merged automatically: the new game folders, and main's TOTK runtime, scripts and tests. | — |

## 4. Verification
Run on the merged tree:
- **Seven CI C tests (UBSan):** `test_romfs_paths`, `test_feedback_settings`, `test_controller_map`, `test_keyboard_map`, `test_game_language`, `test_audio_ramp` and `test_bow_state` all pass.
- **`python3.14 -m unittest discover -s tests`:** 407 tests ran and 6 were skipped. Five modules (`test_botw_import`, `test_dlc_import`, `test_game_containers`, `test_spin_waits`, `test_updates`) fail to import because `cryptography`/`capstone` are not installed for python3.14 on this Mac. They failed the same way before the merge. Everything else passes, including:
  - the settings panel probe;
  - the AppKit probes `settings_controller`, `command_q`, `text_keyboard`, `mouse`, `gamepad_type`, `hid_imu` and `switch_left`.
- **`make probe-input`:** passes. Its gyro check had failed on `sqhh99` before; main updated the probe for the 5 ms clock.
- **`make probe-input-file`:** passes after the stub was added.
- **Compile check:** `frontend.m`, `gamepad.m` and `gamepad_feedback.m` were compiled with `-fobjc-arc -Wall -Wextra -Werror -fsyntax-only` for both `TOTK_GAME_V143` and `TOTK_GAME_BOTW_V190`. `input.c`, `services.c`, `loader.c` and `threads.c` were compiled the same way for 1.4.3. No errors.

Not run:
- **Full `make runtime-v143` link:** it needs `games/totk/.venv`, which does not exist in this checkout.
- **App rebuild:** `build/build_game.py` was not run for either game.
- **iOS build:** no iOS SDK is installed.
- **New ports:** the `acnh`, `eow` and `unicorn` ports were not built.

## 5. Open items
- Rebuild `build/totk-1.4.3/` and `build/botw-1.9.0/` to try main's input changes (HID rumble and gyro) together with the custom key layout in the game.
- Not pushed to `origin/sqhh99` yet.
