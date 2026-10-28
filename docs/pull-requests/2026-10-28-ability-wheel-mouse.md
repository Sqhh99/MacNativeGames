# PR: fix: the ability wheel keeps the pick the mouse points at instead of springing back to the centre

- **Date:** 2026-10-28
- **Branch:** `fix/ability-wheel-mouse` → `ly05010419/MacNativeGames` `main`. This is an upstream contribution the owner explicitly asked for on 2026-10-28; it is not a personal change, and AGENTS.md's `sqhh99` target applies to personal changes.
- **Base commit:** `aab06fa` (local `main`, synced from upstream by the owner on 2026-10-28)
- **Commit:** `2d0f0f0`
- **Pull request:** [ly05010419/MacNativeGames#1196](https://github.com/ly05010419/MacNativeGames/pull/1196), opened 2026-10-28; verified: open, base `main`, head `Sqhh99:fix/ability-wheel-mouse`, 1 commit, 11 files
- **Related records:** [work log](../work-logs/2026-10-28-upstream-ability-wheel-pr.md); the same fix on `sqhh99`: [work log](../work-logs/2026-10-28-wheel-rotate-arrow-labels.md)

## Related
No existing issue or PR found (searched "wheel mouse", "轮盘", "ability wheel"). The problem: with mouse mode on, holding L (Q on the keyboard) to open Tears of the Kingdom's ability wheel and pointing at an ability with the mouse does not keep the pick. As soon as the mouse stops, the pick springs back to the centre.

## What changed
Mouse mode turns the right stick by "panning": movement adds to a stick deflection that decays every 10 ms (`runtime/mouse_look.h`). That suits the camera. The ability wheel, however, picks whatever the right stick points at, so the decay carried the pick back to the centre whenever the mouse paused.

While L is held, from the keyboard or a controller, the mouse now *points* instead of panning:
- The stick starts at the centre and stays where the mouse puts it.
- Its length is cut to 1, so turning the mouse towards another ability turns the stick at once.
- The mouse turns neither the camera nor the gyro while the wheel is open.
- When L is let go, the stick is centred again, so the camera does not turn on its own after the wheel closes.

Outside the wheel, the mouse behaves exactly as before. Breath of the Wild has no such wheel; the change is compiled out there (`#ifndef GAME_BOTW`).

Implementation:
- `mouse_look.h`: `mouse_look_point` and the pointing state.
- `gamepad.m`: the mouse tick points while L is held.
- `input.c`: publishes the Switch buttons the held keys drive (`runtime_keyboard_buttons`, an atomic, because the mouse ticks under the gamepad's lock, which is taken inside `inputLock`).
- One sentence each in `docs/controls.md` and `docs/controls.zh-CN.md`.

中文：鼠标模式下按住 L（键盘 Q）打开王国之泪的能力轮盘时，鼠标指向的能力会在鼠标停下后弹回中心。现在按住 L 期间鼠标作为指针：摇杆停在指向的位置，松开 L 后回中；轮盘外的鼠标视角不变，旷野之息不受影响。

## Type of change
- [x] Bug fix
- [ ] New feature
- [ ] Performance or refactoring (no behavior change intended)
- [ ] Docs, CI, or build only

## How it was tested
- [x] **Python suite:** `python -m unittest discover -s tests` passes: 465 tests, OK, 5 skipped.
- [x] **CI's native tests:** all 6 pass under UBSan.
- [x] **Probes for the changed parts:**
  - `make probe-input`, `probe-input-file` and `probe-autoload` pass.
  - The mouse-look probe has new pointing checks: starts centred, holds, cut to 1, turns at once, centred at the end, panning afterwards.
  - The mouse-mode probe compiles the real `gamepad.m` and checks that L held from the keys holds the stick with no gyro turn, and that letting go centres it.
  - The `settings_controller`, `text_keyboard` and `gamepad_type` probes pass with the new stub.
- [ ] **Built every game version touched:** only partly.
  - Built: Tears of the Kingdom 1.4.3 with `build_app.py` on macOS; the build's own checks, `--check` and the runtime module probe pass.
  - Not built: Breath of the Wild 1.9.0. Only compile-checked: `frontend.m`, `gamepad.m` and `input.c` with `-Werror` for 1.4.3 and BotW 1.9.0. The other versions were not built either.
  - Not built: `--platform ios`, because no iOS SDK is installed on this Mac. The change sits in shared runtime code (`input.c`, `gamepad.m`, `mouse_look.h`) and needs an iOS build before merge, by someone with the iOS SDK.
- [x] **Played on a Mac:** Tears of the Kingdom 1.4.3, keyboard and mouse with mouse mode on.
  - Before, on a build of `main` at `aab06fa`: holding Q and pointing at an ability, the pick sprang back to the centre once the mouse stopped.
  - After, on this branch: the pick stays until Q is let go, and the camera works normally outside the wheel.

## Checklist
- [x] I have read CONTRIBUTING.md
- [x] No game content, keys or saves; no GPL code or code from other mods
- [x] Existing keys, defaults and verified version tables unchanged. Only the mouse's behaviour while L is held changes.
- [x] Diagnostics are off by default (none added)
- [x] No new host text (one sentence in each controls doc, English and Chinese)
- [x] AI disclosure: Yes. The code, tests and this description were written with Claude Code (Claude Opus 5.5). The owner reproduced the bug on `main` and verified the fix in game; the tests and builds listed above were run.
