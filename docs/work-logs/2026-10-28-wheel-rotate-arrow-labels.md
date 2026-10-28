# Work log: ability wheel with the mouse, Ultrahand rotation from the keyboard, arrow-key labels

- **Date:** 2026-10-28
- **Branch:** `sqhh99`, from `037c39b`; committed as one commit and pushed to `origin/sqhh99` on 2026-10-28 at the owner's request, after the owner confirmed the Ultrahand fix in game
- **Related:** [input remap and settings panel](2026-10-27-input-remap-settings.md), [merge of 2026-10-28](2026-10-28-merge-main.md)

## 1. Request
> While playtesting, I encountered a few issues regarding the controls:
> 1. Holding down the 'F' key brings up a skill-selection radial menu. However, this menu doesn't seem well-optimized for mouse input; often, after I select a skill, the cursor snaps back to the center.
> 2. There is a skill that allows for the manipulation of objects. Once an object is selected, holding the 'R' key is supposed to enable rotation—but regardless of whether I use the mouse or the arrow keys, I am unable to rotate the object.
> 3. In the keyboard settings menu, the text labels for the arrow keys do not align with their corresponding icons; there appears to be an issue with the UI.

A screenshot of the key bindings drawing (Chinese) showed the arrow keys' action labels falling below their half-height keys.

## 2. Plan
1. **Ability wheel.** The mouse drives the right stick by "panning": movement adds to a deflection that decays every 10 ms (`mouse_look.h`). So once the mouse stops, the stick returns to centre and the wheel's pick follows it. Fix: while Switch L is held (the wheel is open), point instead of panning:
   - the stick starts at the centre and stays where the mouse puts it, cut to length 1;
   - the mouse turns neither the camera nor the gyro;
   - the stick is centred again when L is let go.

   This applies to Tears of the Kingdom only; Breath of the Wild has no L wheel.
2. **Ultrahand rotation.** In TOTK, R with the d-pad rotates. The default layout has the d-pad on 2 / 3 / 4 / 5, which the left hand cannot reach comfortably while holding R, and the arrows only turned the camera. Fix: while mouse mode is on (the mouse is the camera) and R is held, the camera inputs drive the d-pad in their direction. With mouse mode off they stay the camera, because a throw (R held) is aimed with them.
3. **Arrow-key labels.** Half-height keys used the full-key layout: the name on top and the action below it, which overflowed a 22-pt key. Fix: on a half-height key, draw the name and the action on one line.
   - The four arrow keys share one font size.
   - A closing arrow that repeats the key's own symbol is dropped (↑ 视角 rather than ↑ 视角 ↑).
   - The short Japanese camera labels become 視点 (the usual word in Japanese games), so they fit like the Chinese ones.
4. Add tests, update the docs, rebuild the TOTK app and validate it.

## 3. Files changed
| File | Change | Addresses |
|---|---|---|
| `games/totk/runtime/mouse_look.h` | `pointing` state and `mouse_look_point`. While pointing, movement is held and cut to length 1, with no decay and no gyro; the stick is centred on entry and exit. | 1 |
| `games/totk/runtime/gamepad.m` | The mouse tick turns pointing on while L is held by the keys, the mouse buttons or a controller (`runtime_keyboard_buttons()` combined with the controller's mapped buttons). Not compiled for BotW (`#ifndef GAME_BOTW`). | 1 |
| `games/totk/runtime/input.c`, `runtime.h` | `runtime_keyboard_buttons()`: the layout's held Switch buttons, published through an atomic. `input.c` reads controller state while holding `inputLock`, so the gamepad timer must not take that lock. The layout now gets `runtime_mouse_enabled()`. | 1, 2 |
| `games/totk/runtime/keyboard_map.h` | `keymap_apply(..., mouse_camera)`: in mouse mode, R with camera inputs is R with the d-pad. The header comment describes the rule. | 2 |
| `games/totk/runtime/bindings_diagram.h` | One-line layout for half-height keys (`DIAGRAM_HALF_H`, `diagram_half_action`, `diagram_half_action_rect`), one shared size for the four arrows, the repeated arrow dropped, Japanese camera labels changed to 視点. | 3 |
| `tests/test_keyboard_map.c` | R + arrows in mouse mode (one and two directions), arrows alone, no mouse mode, moving unchanged. | 2 |
| `games/totk/tests/mouse_look/probe.c` | Pointing: starts centred, holds, cut to 1, turns at once, centres at the end, panning afterwards. | 1 |
| `games/totk/tests/mouse/probe.m` | The real `gamepad.m`: L from the keys holds the stick with no gyro turn; letting go of L centres it. | 1 |
| `games/totk/tests/{command_q,gamepad_type,text_keyboard}/probe.m`, `games/totk/scripts/{input,input_file,autoload}_probe.c` | Stubs for `runtime_keyboard_buttons`, `runtime_mouse_enabled` and, in `autoload_probe.c`, `runtime_setting_remove`. | builds |
| `docs/controls.md`, `docs/controls.zh-CN.md` | The rotation rule next to the bow rule; the ability wheel exception in the Mouse section. | 1, 2 |

## 4. Verification
Run:
- **CI C tests (UBSan):** all seven pass (`romfs_paths`, `feedback_settings`, `controller_map`, `keyboard_map`, `game_language`, `audio_ramp`, `bow_state`). The keyboard-map test includes the new rotation cases.
- **Python suite:** `build/totk-1.4.3/work/venv/bin/python -m unittest discover -s tests` ran 469 tests: OK, 5 skipped. This covers:
  - the mouse-look and mouse-mode probes, including the new pointing checks;
  - the settings panel probe;
  - the `settings_controller`, `command_q`, `text_keyboard` and `gamepad_type` probes.
- **Input probes:** `make probe-input`, `make probe-input-file` and `make probe-autoload` pass.
- **Compile check:** `frontend.m`, `gamepad.m` and `input.c` pass `-fsyntax-only -Werror` for 1.4.3 and for BotW 1.9.0.
- **Drawing:** a scratch copy of the settings panel probe rendered the key bindings drawing in English, Chinese and Japanese. The arrow labels sit inside their keys on one line, at the same size. The scratch probe is not committed.
- **App build:** `python3.14 build/build_game.py totk-1.4.3` completed: 31,307 shaders compiled in 52 s, about 1.5 minutes in all. The runtime `Contents/Resources/totk/build/totk-native` contains the new 視点↑ label, so it was built from the working tree.
- **App metadata:** `CFBundleShortVersionString` 1.4.3; `MNGSourceCommit` 037c39b, the base commit, because the changes are uncommitted.
- **Final checks:** `LSMinimumSystemVersion` was 26.0 against a binary minimum of 27.0. It was set to 27.0 and the app ad-hoc re-signed. Then all passed: `codesign --verify --strict`, `Contents/MacOS/TOTK --check` ("ok: game version 1.4.3") and `update_runtime.probe_runtime(..., "v143", ...)`.

Not run:
- **Gameplay:** nobody has played with the changes yet. The owner is testing the wheel, Ultrahand rotation and the drawing in the game.
- **BotW:** the app was not rebuilt (the issues were reported in TOTK). Its source was only syntax-checked.
- **iOS:** no iOS SDK is installed, so the iOS build was not run.
- **DMG:** not repackaged.

## 5. Open items
- **Gameplay check:** confirm in game that the wheel keeps the pick and that R + arrows rotates.
- **Ultrahand rotation assumption:** the fix assumes rotation is R + d-pad, from the game's controls. With motion controls on, the mouse's gyro may also rotate while R is held; not tried.
- **Pointing scope:** pointing applies whenever L is held. A short L tap (use the current ability) freezes the mouse camera only for that tap.

## 6. Follow-up request: the view jitters while Ultrahand holds an object
> There is another issue: after selecting an object, controlling the viewpoint with the mouse doesn't work correctly—the view jitters and doesn't respond as it should to my mouse movements.

### Cause
In mouse mode, each movement drives both the right stick and a synthetic gyro (`mouse_look.h`). The ordinary camera reads only the stick. The aim cameras (Ultrahand holding an object, the bow) also read the gyro. The 1.2.1 notes in `game_patches.c` record that the Ultrahand aim update reads gyro velocity each frame.

AppKit coalesces mouse moves to the display rate (60–120 a second), while the gyro tick runs every 10 ms. So a tick received one move, two or none, and its rate was the movement inside that tick.

A simulation through the real header, a steady pan with 60 Hz moves, read as a gyro rate alternating between 0.375 and 0 rev/s on every tick (82% spread around the mean). At 120 Hz the spread was 31%. The stick, which holds and decays its deflection, stayed within about 7%. That matches jitter in the aim cameras only.

### Fix
`mouse_look_move_at(..., now_ns)`, which `gamepad.m` calls with `runtime_now_ns()`:
- Each move's turn is kept pending, and the mouse's speed is measured as movement over the time between moves, averaged over about 20 ms.
- Each tick releases the pending turn at that speed, with a gain of 0.1 toward keeping one move's worth pending.
- The total turn is exactly the mouse's.
- A move more than 50 ms after the previous one, or an untimed `mouse_look_move`, is released at the next tick as before.

Compared in simulation:
- An exponential release: 24–31% spread at 60 Hz, with lag.
- A 2–4-tick moving average: 20–33% spread.
- Releasing at 1.25× the speed: 33% spread.
- The chosen speed-paced release with a reserve: 6–8% at 60 Hz, 9–14% at 90–144 Hz, and the turn ends about one move after the mouse stops.

### Files
| File | Change |
|---|---|
| `games/totk/runtime/mouse_look.h` | `speed`, `reserve`, `moved_ns`, `mouse_look_move_at`, paced release in the tick; the header comment explains why. |
| `games/totk/runtime/gamepad.m` | Mouse moves are timed. |
| `games/totk/tests/mouse_look/probe.c` | 60 Hz moves: untimed, the rate jumps (over 50% spread); timed, it is steady (under 12%), the turn ends within two ticks, and the total turn is exact in both. |
| `docs/controls.md`, `docs/controls.zh-CN.md` | One sentence in the Mouse section. |

### Verification
- **Tests:** the seven CI C tests, `make probe-input`, and the Python suite (469 tests, OK, 5 skipped) all pass.
- **Rebuild:** `python3.14 build/build_game.py totk-1.4.3` completed (31,307 shaders in 50 s). The work copy's `runtime/mouse_look.h` and `gamepad.m` contain the change, and `totk-native` was rebuilt at 03:58 after the edit.
- **Final checks:** `LSMinimumSystemVersion` set to 27.0 and the app re-signed again. Strict `codesign`, `--check` and `probe_runtime` pass.
- **Not run:** gameplay; the owner is testing.

### Open
The stick and the gyro both still turn the aim camera. If Ultrahand or the bow still feels off (for example, drifting after the mouse stops), the stick's decay is the next suspect. To compare: turn off gyro aiming in the settings panel, then turn mouse mode off and on (the mouse reads the gyro switch when mouse mode turns on). The aim cameras then get the stick only.

## 7. Follow-up: the pacing did not fix it; the mouse no longer drives the gyro by default
> The problem still exists, I just tested

The owner's answers to two questions:
- **Symptom:** "Shakes while moving" and "Overshoots / drifts". "When I turn on the skill and the target is not selected, there is no problem with the movement of the perspective. When I select the object, the perspective of the mouse will shake when I move it."
- **Gyro off:** "I can just turn off somatosensory aiming, that seems to be the reason".

The saved settings were mouse sensitivity 100 (the mouse's gyro scales with it) and gyro on.

### Conclusion
Once an object is held, TOTK moves the view with the gyro as well as the stick. The mouse driving both (a synthetic gyro plus the decaying stick) shakes the view and carries it past the aim; pacing the gyro (section 6) did not remove that. With the mouse on the stick alone, the view behaves (owner's test with gyro aiming off).

### Change
The mouse's gyro is now opt-in:
- `gamepad.m` `mouse_apply`: `gyro = runtime_gyro_enabled() && TOTK_MOUSE_GYRO == "1"`; previously it was on unless `TOTK_MOUSE_GYRO=0`.
- A controller keeps its own gyro while mouse mode is on (`runtime_motion_mouse(0)`), so the panel's gyro-aiming switch can stay on for controllers.
- The pacing from section 6 stays, for `TOTK_MOUSE_GYRO=1`.
- The other games' own copies of `gamepad.m` (`wonder`, `odyssey`, `ssbu`, `mvdk`) are separate ports and were not touched.
- BotW shares this runtime, so its mouse no longer turns the gyro by default either.

### Files
| File | Change |
|---|---|
| `games/totk/runtime/gamepad.m` | Opt-in gyro, and the comment explaining why. |
| `games/totk/runtime/mouse_look.h` | The header says the gyro part needs `TOTK_MOUSE_GYRO=1`. |
| `games/totk/tests/mouse/probe.m` | The gyro checks run with `TOTK_MOUSE_GYRO=1`. New checks: by default the stick only (`runtime_motion_mouse(0)`, no feeds), and `=0` behaves the same. |
| `docs/controls.md`, `docs/controls.zh-CN.md` | The Mouse section describes the default and `TOTK_MOUSE_GYRO=1`. |

### Verification
- **Tests:** the seven CI C tests and the Python suite (469 tests, OK, 5 skipped) pass, including `tests.test_mouse`.
- **First rebuild:** `python3.14 build/build_game.py totk-1.4.3` completed, and the work copy has the change. Its shader warm-up was skipped because a settings-panel test running at the same time held Metal's cache.
- **Second rebuild:** run with no test process left; 31,307 shaders compiled in 50 s.
- **Final checks:** `LSMinimumSystemVersion` was 26.0 again after the build; set to 27.0 and re-signed. Strict `codesign`, `--check` and `probe_runtime` pass.
- **Not run:** gameplay; the owner is testing.

### Open
The local build wrapper resets `LSMinimumSystemVersion` to 26.0 on every build, so each build needs the correction and a re-sign.

## 8. Outcome
- **Owner's test, 2026-10-28:** "The issue has been resolved." Holding an object with Ultrahand and moving the view with the mouse now works.
- **BotW:** shares the runtime, so the stick-only mouse also applies to it. Its app at `build/botw-1.9.0/` predates these changes and was not rebuilt.

## 9. Follow-up: issue 4's changes reverted
> Regarding Issue 4: Since this problem is caused by enabling the "motion aiming" feature—rather than being a code defect—I believe the changes made for Issue 4 should be reverted in the `sqhh99` branch.

The owner established on a build of upstream `main` (see [the upstream PR log](2026-10-28-upstream-ability-wheel-pr.md)) that the Ultrahand shaking comes from having motion aiming on; with it off, the view is fine. So both changes made for it (sections 6 and 7) are reverted:
- **Mouse gyro default:** on again unless `TOTK_MOUSE_GYRO=0`, as upstream. Opt-in (`=1`) is gone.
- **Gyro pacing:** `mouse_look_move_at`, the speed/reserve fields and the paced release are removed. The mouse moves through `mouse_look_move` and its gyro goes out at the next tick, as upstream.

The other fixes stay: the wheel pointer (issue 3), R + arrows, and the arrow-key labels.

### Files
| File | Change |
|---|---|
| `games/totk/runtime/mouse_look.h` | Taken from the upstream PR commit `2d0f0f0`: upstream's file plus the wheel pointer only. |
| `games/totk/tests/mouse_look/probe.c` | Taken from `2d0f0f0`: the pacing checks are gone, the pointing checks stay. |
| `games/totk/runtime/gamepad.m` | The mouse-mode comment and the `gyro =` line back to the `037c39b` text; `runtime_mouse_move` calls `mouse_look_move`. |
| `games/totk/tests/mouse/probe.m` | No `TOTK_MOUSE_GYRO=1` at the start; the `TOTK_MOUSE_GYRO=0` check is back as it was. The wheel check stays. |
| `docs/controls.md`, `docs/controls.zh-CN.md` | The gyro sentence and the `TOTK_MOUSE_GYRO=0` note back to the `037c39b` text. Against `037c39b`, the docs now differ only by the rotation and wheel sentences. |

### Verification
- **Tests:** the seven CI C tests, `probe-input`, `probe-input-file`, `probe-autoload`, and `gamepad.m -fsyntax-only -Werror` for 1.4.3 and BotW 1.9.0 all pass. The Python suite ran 469 tests: OK, 5 skipped.
- **App:** not rebuilt. `build/totk-1.4.3/Tears of the Kingdom.app` still has the stick-only mouse until the next build.

## 10. Follow-up: both apps rebuilt, DMGs packaged, records committed
> Yes, please rebuild the project and create a commit. Also, could you please build the .dmg files for both games as well?

### Builds from `5c57e25` (local wrappers; each app's `MNGSourceCommit` is `5c57e25`)
- **TOTK 1.4.3:** `python3.14 build/build_game.py totk-1.4.3` completed in 880 s. 31,307 shaders were compiled again (844 s), because the cache for this location had gone cold after the upstream test build.
- **BotW 1.9.0:** `python3.14 build/build_game.py botw-1.9.0` completed in 248 s (21,228 shaders, 222 s). This is BotW's first build with the 2026-10-28 changes; its runtime contains the new 視点 label.
- **Order:** the two builds ran one after the other. Packaging started only after both had finished, so nothing held Metal's cache during a warm-up.

### DMGs (`python3.14 build/package_game.py <game>`)
Before packaging, the wrapper:
- ran `probe_runtime`;
- checked `CFBundleShortVersionString` and that no `.keys` file is bundled;
- set `LSMinimumSystemVersion` to 27.0, re-signed and ran the launcher `--check` ("ok: game version 1.4.3" / "1.9.0");
- ran `codesign --verify --strict`.

It then ran `hdiutil create` (UDZO) and `hdiutil verify` (checksum VALID).

| DMG | Size | SHA-256 |
|---|---|---|
| `build/totk-1.4.3/totk-1.4.3-arm64-macOS27.dmg` | 17,216,333,252 bytes | `544d5551b99c35da859e5630f1197a5d6c7ab47abecda67991cb65b7f70715cd` |
| `build/botw-1.9.0/botw-1.9.0-arm64-macOS27.dmg` | 15,006,678,418 bytes | `c3aa82f57e8018e7368bcd5a391f74879979158a8f97903753a52462c1ebea33` |

The previous DMGs (2026-10-27, from before these changes) were renamed to `*-arm64-macOS27.2026-10-27.dmg` in the same folders, not deleted. About 94 GiB of disk is free afterwards.

### Commit
This log section, the [PR record](../pull-requests/2026-10-28-ability-wheel-mouse.md) and the [upstream PR work log](2026-10-28-upstream-ability-wheel-pr.md) are committed together and `sqhh99` is pushed.

### Not done
- Gameplay with the rebuilt apps: the revert brings back the upstream gyro behaviour; motion aiming stays off in the owner's settings.
- Installing into Applications: not requested.
