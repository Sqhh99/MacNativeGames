# ACNH: keyboard and mouse layout, settings panel, frame drops

- **Date:** 2026-10-29
- **Branch:** `acnh` (working tree, not committed)
- **Game / build:** Animal Crossing: New Horizons 3.0.1 (experimental), `build/acnh-3.0.1/`
- **AI assistance:** Claude Code (Claude Opus 5.5) wrote the code, tests and this log.

## Request
The owner's request, verbatim:

> I am currently working on the adaptation and configuration for ACNH. While an initial version is already built, I have encountered several issues during gameplay:
> 1. The keyboard and mouse key bindings need to be adjusted to ensure they are ergonomic for players using these input devices.
> 2. The settings panel used in *The Legend of Zelda* can be ported over. This should include views for both keyboard/mouse and controller, as well as options for display quality, frame rate (including a frame rate graph, frame rate capping, and frame interpolation), aspect ratio, and language. Some features may not be applicable to this specific game and can therefore be omitted.
> 3. The frame rate is currently quite unstable during gameplay, often experiencing sudden drops; this requires further optimization.

## 1. Keyboard and mouse layout
The Zelda remappable layer is ported into `games/acnh/runtime` (copied and adapted, not included from `games/totk`, per AGENTS.md):
- `keyboard_map.h` (from `games/totk/runtime/keyboard_map.h`): 24 actions, 2 inputs each.
  - The ACNH default keeps the left hand on the keyboard.
  - The Zelda bow and Ultrahand rules are removed from `keymap_apply`.

  | Action | Keys | Mouse |
  |---|---|---|
  | Move | W A S D | |
  | Camera | arrow keys | |
  | Talk / use tool / confirm (A) | Space | left button |
  | Cancel / run (B) | Shift (hold), Esc | |
  | Pockets (X) | Tab, I | |
  | Pick up (Y) | E | right button |
  | NookPhone (ZL) | Q | |
  | Reactions (ZR) | R | |
  | L / R | Z / C | |
  | L3 / R3 | Control / V | |
  | + | M, Return | |
  | − | Backspace | |
  | d-pad left, up, right, down | 2 3 4 5 | d-pad up (tool ring): wheel click; d-pad left / right: side buttons |

- `input.c`:
  - The player's keys and mouse buttons go through the layout; the layout is loaded from `keyboard.txt`.
  - Key 1 opens the settings panel.
  - Keys 2–4 are no longer shortcuts.
  - Scripted input (`TOTK_INPUT_FILE`, `TOTK_INPUT_SCRIPT`) keeps the old fixed layout, so test scripts are unchanged.
- `frontend.m`: Shift, Control and Option (left and right) come as flag changes; the mouse buttons over the picture are inputs. The pointer is never captured, because ACNH has nothing to aim.
- `controller_map.h` gains `controller_map_target` / `assign` / `format`. A `controls.txt` that does not parse now falls back to the default layout and logs the line, instead of stopping the game.
- `gamepad.m` adds:
  - the settings files next to `controls.txt`;
  - runtime controller remapping;
  - the controller type (auto / Xbox / PlayStation / Switch);
  - L3 + R3 (or a picked button) to open the panel;
  - controller capture while the panel or the text bar is open;
  - battery percent.
- The launcher sets `TOTK_CONTROLS=<data>/controls.txt`, so the panel's files live in `Animal Crossing Data`.

## 2. Settings panel
`settings_panel.h` and `bindings_diagram.h` are adapted from `games/totk`. Pages:
- **Display:**
  - overlay (all / FPS only / off);
  - FPS graph;
  - frame rate: a greyed "30 fps (the game's own rate)" row;
  - frame interpolation: greyed "Not available in this game yet";
  - picture: 1080p, or 1080p + MetalFX upscaling;
  - game language: follow the Mac, or one of 14 languages; from the next launch, via `language.txt` read by `services.c`.
- **Input:** controller type, rumble (`rumble.txt`; in force at once when the run has the vibration devices, otherwise from the next launch).
- **Key bindings:** keyboard + mouse drawing and controller drawing, with ACNH labels and colours, a list view, and per-device resets.

Left out, with reasons:
- **Aspect ratio:** ACNH has no aspect or resolution patch.
- **Frame-rate lock:** ACNH runs at 30 and paces by vsync counts, so a lock above 30 would only repeat pictures.
- **Contribution and star buttons:** the owner's panel preference (AGENTS.md); a test enforces this.

Why interpolation is not offered: the test run below set 30+30 and the log reported "插值帧 0 / 游戏帧 2100 … 缺输入 2100（画面 / 相机 / 深度 / UI）". The MetalFX interpolation hooks find Tears of the Kingdom's passes, not ACNH's, so 30+30 would only pace the game without adding frames. Making it work needs ACNH-specific scene, depth, camera and UI hooks.

The launcher no longer forces `TOTK_MFX_UPSCALE=0` / `TOTK_MFX_OUTPUT=0`; both still default off. Before this change, the panel's Picture row would always have been locked.

New diagnostic: `panelshot <page 0-3> <path>` in the command file draws the panel to a PNG.

## 3. Frame drops: diagnosis
The owner's last session log (`build/acnh-3.0.1/Animal Crossing Data/last-run.log`, about 10 minutes, 17,100 frames):
- Steady state is a flat 30 fps: frame time p50 33.33 ms, GPU about 2 ms.
- 26 frames took over 50 ms. In 25 of them, most of the time was new pipelines and shader libraries compiled on the submit thread: 17.9 s of the 19.2 s lost.
- Worst frame: 6.1 s, with 58 pipelines and 61 shader libraries.
- The app carried no shader seed ("No bundled shader seed"), and the pipeline archive was empty on that run.

Feasibility probe (scratch script, not part of the build):
- The game's own shader containers give 6,396 shaders. Their runtime keys match directly, with no control-section rewrite:
  - `Shader/Park_UBER_All` and the other `Shader/` archives: 3,409;
  - `Effect/`: 2,522;
  - `Model/`: 326;
  - `Layout/`: 144;
  - the `main` module: 40.
- Together they cover 405 of the 474 shaders the owner's sessions met (85%).
- In the cache, every vertex variant has `depth_minus_w: true` and every other stage false. A seed has to mark its vertex rows the same way, as Odyssey's does.

## 4. Frame drops: the shader seed
The owner approved the size and first-launch cost ("yes!", 2026-10-29).

**`games/acnh/tools/prepare_shader_seed.py`** is new. It is adapted from TOTK's tool (container parsing, the seed format) and reads no other game's files.
- **Input:** the prepared RomFS (`romfs.bin` with `index.json`) and the rewritten modules.
- **Translation:** each shader is translated with the pinned `totk_xlate`, using the runtime's own requests and variant names.
- **Shadow maps:** shaders that report shadow-compare slots get a second variant with depth textures bound there.
- **Output:** `<native work>/build/shader-seed`, reused while its identity holds (chain, RomFS SHA-256, translator and tool hashes).
- **3.0.1 result:**
  - 6,470 shaders found: Shader 3,404, Effect 2,522, Model 326, Layout 144, Swkbd 40, main 34;
  - 1,455 depth variants;
  - 0 failures;
  - 22,321 files, 452 MB, 35 s.

**`package_native_app.py`** checks the seed (chain, RomFS identity, every file hash) and clones it to `Resources/game/build/shader-seed`. It adds the link `Contents/MacOS/shader-seed` for the warm-up list. Without a seed it packages as before and says so. The README documents the step.

**Offline coverage** against the owner's cache: the seed serves 383 of the 475 variants the owner's sessions needed (81%). Of the rest:
- 69 are in no game file;
- 23 use other bind states.

These still translate during play.

**Test sessions** (agent sessions with scratch data, fresh shader caches, A pressed every 2 s for 120 s after the first frame; title and new-game intro only):
- **With the seed:**
  - the seed was imported in about 1 s (22,321 files);
  - the first frame came after 210 s, because with no earlier list of its own the first launch compiles all 7,925 libraries before the title;
  - 69 shaders were translated during the session;
  - 10 frames took over 50 ms, 0.5 s lost in total, the worst 145 ms.
- **With the seed off** (`TOTK_SHADER_SEED=off`):
  - 206 shaders were translated during the session;
  - 8 frames took over 50 ms, 0.5 s lost in total, the worst 180 ms.
  - The hitch counts do not compare: both sessions ran after the first one had filled Metal's own compile cache for this app, so neither recompiled from source. The translation counts are the measure that cache does not affect.
- **Relaunch of the seeded data:** first frame after 1 s; the warm-up of 7,994 shaders finished in the background in 1.06 s.

**Not measured:** play on the owner's island. The hitches of the owner's session (17.9 s of compiling) came from shaders met for the first time; whether they are gone there is the owner's test. On the owner's data folder, `pso_user.tsv` already exists and is warmed first, so the title should come quickly; the seed warms in the background, and entering the world waits up to 15 s for it (`mtl_warm_wait`).

## 5. App icon and the keyboard drawing (owner's test, same day)
The owner reported, verbatim: "There are two issues: 1. The game icon is not displaying correctly. 2. In the settings menu, the keyboard layout view has some UI issues: the "Esc" key label is missing, and the key positions are misaligned." (with a screenshot)

**Icon.** The packager only bundles `<native work>/build/AppIcon.icns`, and nothing in the ACNH flow made one, so the 3.0.1 app had no icon (this predates this work). The new `games/acnh/tools/extract_app_icon.py`:
- reads the update NSP's Control RomFS with `prepare.py`'s reader and IVFC check;
- requires its `control.nacp` to equal the prepared one;
- takes `icon_AmericanEnglish.dat` (a 256x256 JPEG);
- makes the `.icns` with `sips` and `iconutil`.

The README has the step. The icon was looked at (the game's title art) and is bundled as `AnimalCrossingIcon.icns`.

**Keyboard drawing.** Two causes, both in the screenshot:
- **Esc:** the function-key row is 0.72 of a key high, and esc's two-line action ("Run / Cancel") ran over the key below. Keys in that row now write the action on one line, shrunk to fit. A `panelshot` of the page confirms it.
- **Misalignment:** the panel was 90% opaque, and the game's own letter keyboard (the name entry) showed through the drawing. The panel background is now opaque. `panelshot` draws only the panel, so this part was not checked against the game behind it.

## 6. Crashes, the Finder icon, saving (owner's test, same day)
The owner reported, verbatim:

> A few more issues:
> 1. The game keeps crashing. It crashes consistently in certain spots—for instance, after I set up a tent, the game crashes whenever I click on the mailbox. This has happened twice now. The game also crashed frequently during the initial setup phase; while some fixes have improved things, the crashes still happen quite often.
> 2. The game app icon—or perhaps the file icon—doesn't seem to be displaying correctly, though the icon for the running application appears fine.
> 3. Is there a save feature? Every time I launch the game, I have to go through the tutorial again, which is quite inconvenient.

**Crash.**
- The owner's `last-run.log` ends with `sm: service "pctl" not implemented` and `FAIL: IPC service not implemented`. The call chain names `nn::pctl::CheckFreeCommunicationPermission(bool)` → `nn::pctl::detail::ipc::GetService()`: the mailbox asks the parental controls whether letters are allowed.
- An earlier crash record (`build/acnh-3.0.1/work/crash-records/20261029-033827`) is the same failure, reached from another game path.
- Only the last two logs are kept, so the owner's earlier setup crashes could not be read.

**Audit of unhandled imports.** Every SDK function `main` and `subsdk0` import that no host override names was listed. The ones single-player play can reach now have host versions:
- `runtime/system_applets.c` (new):
  - `nn::pctl`: `IsFreeCommunicationAvailable` and `CheckFreeCommunicationPermission`, allowed;
  - `nn::err::ShowError` (three forms): logged;
  - `nn::ec::ShowShopApplicationInformation`: logged;
  - `nn::album`: Initialize, Finalize, SaveScreenshot (1280x720 RGBA written as PNG to `Animal Crossing Data/Screenshots`), SaveAndShareScreenshot (saved only), GetSharePostedLastUrl (none);
  - `nn::account::LoadProfileImage`: a generated 256x256 JPEG.
- `fs_host.c`:
  - `Commit` with options;
  - `GetDeviceSaveDataSize` and `ExtendDeviceSaveData`: NACP size 0x6f00000 at the start, at most 0x24000000 (the update's NACP), remembered in `profile/device-save-size.txt`;
  - `GetSaveDataRestoreFlag`: false;
  - `RenameDirectory`;
  - `GetDirectoryEntryCount`.
- `account.c`: `OpenUser`, `ListQualifiedUsers`, `PromoteQualification`, and the online-licence dialog, which is logged.
- Left as they were (online or local-wireless only): `nn::ldn`, `nifm` IP and local mode, `ssl`, `nsd`, the `friends` and `account` async contexts.

**Saving.**
- The owner's save folder (`profile/save/a5b5…`) is empty, and the launcher's five backups of it are empty too: the game never saved.
- Animal Crossing's first save is the automatic one at the end of the first day, after the evening welcome, which comes after the tent and mailbox step. The crash came before it.
- The port's save path is the existing `fs_host.c` device save; 3.0.1 also needs the save-size and commit-with-options calls above, so a save would have hit those next.
- Whether the first save now completes was not played.

**Icon.** `NSWorkspace iconForFile` on the bundle returns the title icon, so the Finder showing the old one was its cache for that path. The packager now sets the bundle's modification date and re-registers it with Launch Services (`lsregister -f`) after packaging.

## 7. Chinese input crash, and more crash checks (owner's test, same day)
The owner reported, verbatim: "There is also a crash. When I input a name on the keyboard, if it is the Chinese input method, when inputting Pinyin in Chinese, there will usually be many candidate Chinese characters above the keyboard. At this time, if my selection reaches the upper boundary of the key selection area, I will continue to move the keyboard selection upward. Select, the game will crash and crash. That is to say, after inputting Pinyin, if there are candidate Chinese characters on the keyboard and it is in a confirmed state, the game will crash and crash. Check this problem and continue to check the game to see if there are other problems that may cause the crash."

**Cause.** Both of the owner's last logs end with `FATAL TOTK shader a4400225…: unsupported NVN stage 2` from `prog_get`, which aborts.
- Stage 2 is a geometry shader, which Metal does not have.
- A scan of every shader container, including the geometry and tessellation slots, finds them only in the name keyboard's own UI shaders (`Swkbd/shader/*OceanShader*`). None are in `Shader/`, `Effect/` or `Layout/`.
- The game imports no `nn::swkbd` function: the keyboard is drawn by the game.

**Fix (`nvn_mtl.m`).**
- A program with a geometry or tessellation stage is marked missing for good (`unsupported`) instead of ending the game, and the log names it once.
- Its draws are skipped as an untranslated program's draws already are.
- `prog_resolve` never tries to translate such a stage.

**Reproduced and verified** in an agent test session (scratch data, `TOTK_LANG=zh-Hans`, scripted keys):
- The game reached the name entry; in Pinyin mode "a" was typed, and the cursor moved up into the candidate row and past its top edge.
- Both geometry programs came up (`a4400225…`, `b104bb9f…`) and were logged as skipped; the game kept running.
- The candidate row's highlight still showed, and A entered "啊" as the name.
- The same session then went on with A presses for 5 minutes, through the airport, the flight and the arrival speech on the island: no fatal error.
- The tent, mailbox and first-save steps need walking that was not scripted.

**Further checks.** The remaining unhandled imports from the audit in section 6, on the online and local-play paths, now answer as unavailable or do nothing:
- `nifm::SetLocalNetworkMode` and `GetCurrentIpConfigInfo`;
- the five `ssl::Context` / `Connection` functions;
- `nsd::ResolveEx`;
- `hid::MergeSingleJoyAsDualJoy`.

`test_acnh_host_imports.py` pins all of them and the geometry skip.

**Still not covered:**
- local wireless play: `nn::ldn` goes to the host's `ldn:u` service, whose commands were not checked;
- visual-only gaps logged in red: logic op and alpha test are not implemented on Metal, and the geometry-shader draws are skipped.

## 8. Owner's test and commit
The owner, verbatim: "Testing is complete; it seems to be working fine now. Thanks for your help—please go ahead and commit the changes, then push the code."
Committed on `acnh` and pushed to `origin/acnh` at their request. ACNH 3.0.1 stays experimental: this records the owner's play test and the checks below, not a verified release.

## Validation actually run
- `python -m unittest discover -s games/acnh/tests`: 37 tests OK at the end (adds `test_acnh_host_imports.py`, which pins the override names), including the new `test_acnh_shader_seed.py` (synthetic BNSH keys, runtime variant names and requests, shadow variants, chain) and `test_acnh_input.py`:
  - the C probe of both layouts;
  - the README table matches the default layout;
  - the panel's language list matches `services.c` and `system_services.c`;
  - no contribution or star button;
  - no other-game includes;
  - scripted input keeps the fixed layout.
- `make check` with the work venv: pass on the first runs. On the last run, after the crash fixes, one error: `test_builder_mod_archive`'s `test_a_cancel_kills_tar`, a repository-level tar timing test outside ACNH; an earlier session's log shows the same failure on a plain `main` base.
- `acnh-native rewritten probe-save`, run in the native work folder: pass, 28 checks, including the six new save functions; `TOTK_PROBE_NEGATIVE=23` fails as it should.
- `build_host.py`, `prepare_shader_seed.py` and `package_native_app.py` (README commands, existing work folders): all pass; the packager reports "Bundled the shader seed: 6470 shaders, 22321 files" and "Successfully packaged and verified". The app is 10 GB.
- App checks:
  - `codesign --verify --strict --deep`: ok;
  - `LSMinimumSystemVersion` 27.0, binary minos 27.0;
  - launcher `--check`: ok;
  - `run_native_probe.py probe-startup`: pass (phase 4, version 3.0.1).
- Test launch (agent session, scratch data folder, not the owner's save):
  - the panel's four pages were drawn with `panelshot` and looked right;
  - a relaunch restored the saved choices: `language.txt` = ja (the game showed Japanese), `keyboard.txt`, `controls.txt`, overlay, FPS graph, and `graphics-output.txt`, with MetalFX output 1920x1080 → 2316x1303 and a clean picture;
  - interpolation made 0 frames (see above).
- Not run:
  - gameplay on the island with the new layout;
  - mouse clicks and the panel's controls driven by hand (the owner's test);
  - a controller (none connected);
  - the iOS frontend (`frontend_ios.m`, not part of the ACNH build), which lacks the new panel functions.

## Not included
The untracked `docs/work-logs/2026-10-28-merge-main-build-dmgs.md` belongs to another session and was left alone.
