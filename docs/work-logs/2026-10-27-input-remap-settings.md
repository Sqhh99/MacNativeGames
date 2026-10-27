# Work log: keyboard, mouse and controller remapping, mouse sensitivity, interface language, settings panel layout

- **Date:** 2026-10-27
- **Branch:** `sqhh99` (from `sqhh99` at `9bfca60`; the work was done on a local branch `feat/input-remap-settings` with no commits of its own and committed directly to `sqhh99`)
- **Related:** no code review archive and no PR record (committed and pushed to `sqhh99` directly, at the owner's request)

## 1. Request

> Please take a look at this project; the following modifications are required:
>
> 1. Optimize the game's key bindings: remove redundant keys and implement support for custom key mapping.
>
> 2. Add a toggle/adjustment for mouse sensitivity. Currently, the game only allows for the adjustment of camera rotation speed; there is no way to change the mouse movement speed during gameplay. This should be implemented in the settings menu using a slider.
>
> 3. The initial screens—such as the shader pre-compilation and pipeline setup screens—currently default to English. The menu that appears when pressing the '1' key is also in English by default. Please add a language selection option (English, Japanese, and Chinese), with English set as the default.
>
> 4. Remove the version number from the performance information display; instead, place it in the bottom-left corner of the menu that appears when pressing the '1' key. Also, remove the key prompts at the very bottom of the screen and adjust the bottom spacing and margins accordingly.
>
> 5. The current key mapping is poorly designed. Based on my experience playing games with a keyboard: the 'Esc' and 'Tab' keys currently perform the same function. Conventionally, 'Esc' should open the system settings menu. 'Enter' or 'E' should be used for "Confirm" (instead of 'J'), while 'Backspace' or 'Q' should be used for "Cancel" (instead of 'K'). Sprinting should be mapped to 'Shift'. Furthermore, for players using a keyboard and mouse (left hand on the keyboard, right hand on the mouse), having to press 'J' or 'K' to confirm an action is extremely inconvenient. The mouse should be reserved for movement, aiming, attacking, and defending; the keyboard layout should allow the left hand to handle all other inputs, so the player doesn't have to stop using the mouse to reach for the keyboard—this is a matter of basic gaming ergonomics. Additionally, the 'Q' key or the mouse scroll-wheel button should be used for locking onto enemies.
>
> 6. The menu that appears when pressing the '1' key needs to be optimized. It should include an interface for remapping keyboard/mouse and controller inputs. An intuitive layout that clearly displays the current key assignments would be ideal, and a "reset to default" function should also be included.

A new default keyboard and mouse layout for left hand on the keyboard and right hand on the mouse; remapping of keyboard, mouse and controller in the key-1 settings panel with resets; a mouse sensitivity slider; an English / 中文 / 日本語 interface language, English by default; the version moved from the overlay to the panel's bottom-left corner, without the panel's bottom key hints.

## 2. Plan

1. Read the input path (`runtime/input.c` fixed key table, `runtime/controller_map.h` / `runtime/gamepad.m` for controllers and mouse buttons, `runtime/mouse_look.h`), the panel (`runtime/settings_panel.h`), the HUD box (`runtime/frontend.m`) and the host-text helper (`totk_ui_lang.h`), and the tests that pin them.
2. Add a pure-C keyboard and mouse layout (`runtime/keyboard_map.h`): actions (16 Switch buttons, 8 stick directions), two inputs each, the new default, a parser and writer for `keyboard.txt`, swap-on-bind, and the bow rule (attack while ZR is held shoots, as the earlier `mouse_right = zr aim mouse_left`).
3. Route window keys and mouse buttons through it (`runtime/input.c`); keep the old fixed table for scripted input so test scripts and auto-load keep their meaning. Move the mouse buttons' defaults out of the controller layout; mouse lines in `controls.txt` still work.
4. Add a writer for the controller layout and get / set / reset APIs (`controller_map.h`, `gamepad.m`), a persistent mouse sensitivity (`mouse-sensitivity.txt`, `TOTK_MOUSE_SENSITIVITY` still decides), and all six modifier keys as layout keys (`frontend.m`).
5. Three interface languages in `totk_ui_lang.h`: a shared choice (`ui-language.txt`, read by `frontend.m` and `app/launcher.m`), English by default on the Mac, `TOTK_UI_LANG` still decides; Japanese for existing texts from a table keyed by the English, `TOTK_UI3` for new texts.
6. Rewrite the settings panel: tabs Display / Input / Key bindings (L1 / R1 on a controller), the language row, the sensitivity slider, the key bindings table with capture, clear, swap and two resets, the version in the bottom-left corner, no bottom hints; remove the commit line from the HUD box.
7. Update tests, probes, CI and `make check`; add `tests/test_keyboard_map.{c,py}` and `tests/test_ui_language.py`; update `docs/controls*.md` and the keyboard style of `make_button_icons.py`.
8. Build the game binaries and launcher, run the tests, render the panel pages to check the layout.

## 3. Files changed

| File | Change | Addresses |
|---|---|---|
| `games/totk/runtime/keyboard_map.h` (new) | Keyboard and mouse layout: default, parser, writer, bind with swap, apply with the bow rule | 1, 5, 6 |
| `games/totk/runtime/input.c` | Window keys and mouse buttons through the player's layout (`keyboard.txt`); `runtime_keymap_get/set/reset`; scripted input keeps the fixed table | 1, 5 |
| `games/totk/runtime/controller_map.h` | Mouse buttons no longer mapped by default (they belong to the keyboard and mouse layout); `controller_map_format` and `controller_map_target` for the panel | 1, 6 |
| `games/totk/runtime/gamepad.m` | Controller layout get / set (saved to `controls.txt`) / reset; mouse buttons forwarded to the layout; saved, live mouse sensitivity; `runtime_setting_remove` | 1, 2, 6 |
| `games/totk/runtime/runtime.h` | Declarations of the new APIs | 1, 2, 6 |
| `games/totk/runtime/frontend.m` | Commit line removed from the HUD box; Shift / Control / Option left and right as layout keys; language loaded before the boot screen; menu bar follows a language change | 3, 4, 5 |
| `games/totk/runtime/settings_panel.h` | Panel rewritten: three tabs, language row, sensitivity slider, key bindings page, version bottom-left, no bottom hints, Japanese for every row | 2, 3, 4, 6 |
| `games/totk/third_party/d2r_gfx/gfx/nvn/include/totk_ui_lang.h` | English / Chinese / Japanese, English by default on the Mac, shared weak `totk_ui_choice`, `totk_ui_ja` table, `TOTK_UI3` | 3 |
| `games/totk/app/launcher.m` | Launcher dialogs follow `ui-language.txt` | 3 |
| `games/totk/scripts/make_button_icons.py` | Keyboard icon style draws the new default keys | 5 (prompts match the keys) |
| `games/totk/scripts/input_probe.c` | Window-key checks use the new default (E for A, 2–5 for the d-pad) | tests |
| `games/totk/tests/{command_q,gamepad_type,mouse,text_keyboard}/probe.m`, `tests/settings_panel_probe.m` | Stubs for the new APIs; panel probe covers tabs, slider, version label, key bindings, language; mouse probe covers forwarding and sensitivity | tests |
| `tests/test_controller_map.c` | Mouse defaults moved; writer round trip | tests |
| `tests/test_keyboard_map.c`, `tests/test_keyboard_map.py` (new) | Keyboard and mouse layout cases | tests |
| `tests/test_ui_language.py` (new) | Every boot / overlay / launcher `TOTK_UI` text has Japanese with the same format arguments | 3 |
| `.github/workflows/tests.yml`, `Makefile` | The keyboard-map test under UBSan in CI and `make check` | tests |
| `docs/controls.md`, `docs/controls.zh-CN.md` | New key table, remapping, sensitivity, panel pages, language, version location | docs |

Default layout chosen (all remappable): E / Return A; Shift / Backspace B; Space X; left click / G Y; right click / Option ZR; Q / wheel click ZL; F L; R R; Control / C L3; V R3; Esc / I +; Tab / M −; 2 3 4 5 d-pad left, up, right, down; W A S D and the arrow keys the sticks. Decisions where the request left a choice: Q is lock-on, not cancel (the request named Q for both; cancel is Backspace or Shift, which is also sprint); Esc opens the game's own menu (+), the host panel stays on key 1; G and Option give attack and the bow a key for play without mouse mode.

## 4. Verification

Run, and passed:
- `tests.test_settings_panel` (the real panel built for 1.0.0, 1.4.3, Breath of the Wild 1.6.0 and 1.9.0, compact and corner HUD).
- `tests.test_text_keyboard` (text keyboard, controller settings with the real `gamepad.m`, Command-Q), `tests.test_mouse`, `tests.test_gamepad_type`, `tests.test_keyboard_map`, `tests.test_controller_map`, `tests.test_ui_language`.
- Native tests under UBSan: `test_romfs_paths`, `test_feedback_settings`, `test_controller_map`, `test_keyboard_map`, `test_game_language`, `test_audio_ramp`, `test_bow_state`.
- `make build/totk-native-v143 build/totk-native-botw190` in `games/totk` (`-Werror`), and `app/launcher.m` for both games with `-Wall -Wextra -Werror`.
- Panel pages rendered to PNG in English, Chinese and Japanese and looked at.
- Both apps built with `build/build_game.py` (section 6); the owner then played them and reported that the gameplay experience is much better.

Run, and failed for reasons that predate this work:
- `make check`: five test modules cannot import `cryptography` / `capstone` (not installed for `python3.14` on this Mac); `tests.test_state_report` fails the same way on an unmodified worktree of `9bfca60`.
- `make probe-input`'s gyro sampling check fails the same way on `9bfca60`; every keyboard check before it passes.

Not run:
- The iOS build: no iOS SDK on this Mac. The shared code changed (`input.c`, `gamepad.m`, `totk_ui_lang.h`) is plain C / Foundation, but it is not compiled for iOS here.
- Tears of the Kingdom 1.0.0, 1.1.2, 1.2.1 and Breath of the Wild 1.6.0 apps were not built (their panel variants are covered by `tests.test_settings_panel`).

AI disclosure: the code, tests and documentation were written by Claude Code (Opus 5.5) and verified as listed above.

## 5. Open items

- Scripted input keeps the old fixed layout (J A, K B, I X, U Y, Return +, Tab −, F T H G); test scripts were left unchanged on purpose.
- The keyboard button-icon mod draws the default layout only, not a layout changed in the panel.
- Rebinding a controller button in the panel rewrites `controls.txt` and drops comments written there by hand.
- Control with the arrow keys is also macOS's Space-switching shortcut; keyboard-only players may prefer C for crouching.
- The DMGs in `build/botw-1.9.0/` and `build/totk-1.4.3/` still hold the builds made before this work; they were not repackaged.

## 6. Follow-up: build the two games

> Help me build these two games; I’ll test them out.

`python3.14 build/build_game.py totk-1.4.3`, then `botw-1.9.0`, reusing each work folder. Both completed: Tears of the Kingdom 1.4.3 in 31 min (31,305 startup shaders compiled into the Metal cache in 1,805 s), Breath of the Wild 1.9.0 with both add-on packs in 11 min (21,228 shaders in 598 s), each passing the build's own start check. No repository file changed. The apps carry the uncommitted working tree, so their recorded commit is `9bfca60`.

## 7. Follow-up: commit, records and push

> Thank you—the gameplay experience is much better now. Please submit a commit for me under the `sqhh99` branch; include the `agents` directory, organize the documentation based on the skills found therein, and then push the code to the `sqhh99` branch on the remote repository.

- `agents/skills/project-records/SKILL.md` added. It came from another project (FLiNG Downloader: Windows, cargo, pull requests to `main`); its record types, templates and rules are kept, and the project-specific parts are adapted to this repository: the checks (`make check`, probes, `build_app.py`, per-platform testing as in `CONTRIBUTING.md`), pull requests to `sqhh99`, and a PR checklist taken from `CONTRIBUTING.md`.
- This work log written under `docs/work-logs/` as the skill requires; no code review was made and no pull request opened, so there is no review archive or PR record.
- `CLAUDE.md` (made earlier the same day with `/init`) committed with a `Mandatory records` section pointing at the skill, as the skill's "Extending this skill" asks, and corrected for the third native test in `make check`; `AGENTS.md` gained a short `Project records` section so other agents reach the skill too.
- Committed as `Sqhh99 <sqhh99@gmail.com>` on `sqhh99` and pushed to `origin/sqhh99`, together with the four local commits that were already ahead of it (`cc515fc`, `d46ffae`, `29c487a`, `9bfca60`).

## 8. Follow-up: key bindings as drawings

> The current settings interface for mouse, keyboard, and controller is presented as a simple list. I believe the visualization could be improved: for mouse and keyboard mode, for instance, you could display an image of the peripherals with the corresponding key assignments shown directly on them—this would be much more intuitive. The same applies to the controller—showing an image of the controller with the button mappings indicated would also be clearer. You don’t need highly detailed, photorealistic renderings; simple line drawings would suffice. Please go ahead and build the interface, then send me a preview image; if I’m happy with it, you can proceed with the full implementation.

> Wow! This looks really great—let’s go with this and implement it accordingly.

> I encountered a minor issue while playing: in the settings menu, the first option is selected by default, even though I haven’t actually made a selection myself. In my view, an item should only enter a "selected" state after I have explicitly chosen it using my mouse.

Plan: a standalone prototype rendered to PNG (keyboard and mouse; controller in the Xbox and PlayStation layouts) for approval; after approval, the same drawing code as `runtime/bindings_diagram.h`, wired into the panel; the controller highlight made to wait for a controller.

| File | Change | Addresses |
|---|---|---|
| `games/totk/runtime/bindings_diagram.h` (new) | Line drawings of a Mac keyboard with the mouse and of a controller (Xbox / Switch or PlayStation layout), what each key or button does written on it, coloured by kind; hit-testing; the actions nothing drives; English, Chinese and Japanese | drawings |
| `games/totk/runtime/settings_panel.h` | Key bindings page: the drawings with a keyboard-and-mouse / controller switch, a menu of actions on click, "Show as list" for the earlier list; the panel made 960 × 530 on that page only (rebuilt when entering or leaving it), the list when the window is too small; controller navigation of the controller drawing (up / down picks a button, left / right changes it); the controller highlight shown only after a controller moves in the panel, hidden by any click in it | drawings, highlight |
| `games/totk/runtime/keyboard_map.h`, `controller_map.h` | `keymap_assign`, `controller_map_assign`: the drawing's assignment (no swap) | drawings |
| `tests/settings_panel_probe.m`, `games/totk/tests/settings_controller/probe.m` | Drawings, menus, assignment, missing-actions line, device switch, list toggle, size fallback, controller navigation; nothing highlighted at the opening, the first controller input only shows the highlight, a click hides it | tests |
| `tests/test_keyboard_map.c`, `tests/test_controller_map.c` | Assignment cases | tests |
| `docs/controls.md`, `docs/controls.zh-CN.md` | The drawings, how to change a binding, the highlight | docs |

Decisions: the drawings assign without swapping (every key is visible, and the actions left without input are listed under the drawing); the list keeps its swap. A key given to an action whose two slots are full replaces the second. The wider panel is used on the key bindings page only, as proposed with the preview.

Verification: `tests.test_settings_panel` (four game versions), `tests.test_text_keyboard`, `tests.test_mouse`, `tests.test_gamepad_type`, `tests.test_keyboard_map`, `tests.test_controller_map`, `tests.test_ui_language` pass; the keyboard-map and controller-map tests pass under UBSan; `make build/totk-native-v143 build/totk-native-botw190` builds with `-Werror`. The real panel was rendered to PNG (keyboard and mouse in English, the controller in Japanese with a button picked by the controller, the Display page just opened with nothing highlighted) and looked at. The NSMenu itself is not driven in the tests (its items and their effect are); clicking through it was not tried by the agent. Both apps rebuilt afterwards with `build/build_game.py` from this commit's tree: Tears of the Kingdom 1.4.3 in 4 min (31,305 startup shaders in the Metal cache) and Breath of the Wild 1.9.0 in 4 min (21,228), each passing the build's start check; not played by the agent.

Open items: the menu cannot be driven with a controller (the controller drawing changes a button with left / right instead); the keyboard drawing is a US layout, so the letters on an AZERTY or other layout's keys differ from the drawing.
