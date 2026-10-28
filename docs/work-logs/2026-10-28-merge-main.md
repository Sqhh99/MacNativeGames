# Work log: merge local main while preserving the custom settings panel

- **Date:** 2026-10-28
- **Branch:** `sqhh99`, starting at `4773ea0`
- **Merged snapshot:** local `main` at `d1966c5` (23 commits not yet reachable from `sqhh99`, including merge commits)
- **Related:** [previous merge](2026-10-27-merge-main.md), [custom input and settings work](2026-10-27-input-remap-settings.md)

## 1. Request

> 合并一下main分支的代码

Merge the existing local `main` into `sqhh99`, retaining the owner's input, interface and build-layout changes. Do not refresh upstream or push either branch.

## 2. Plan

1. Check the branch and clean working tree, then merge the local snapshot without committing automatically.
2. Resolve the panel, overlay, documentation and probe conflicts by combining upstream behavior with the owner's interface.
3. Run the settings tests, full source checks, new feature probes and both current Mac runtime builds.
4. Record verification and commit the merge as `Sqhh99 <sqhh99@gmail.com>`.

## 3. Files changed

The merge includes upstream graphics-setting persistence, foreground playtime, background update checks, experimental TOTK temporal upscaling, the TOTK 1.4.3 high-FPS fade fix, BOTW rendering optimizations, a default Mac ceiling of 240 FPS and expanded shader/pipeline lists.

| File | Change | Addresses |
|---|---|---|
| `games/totk/runtime/settings_panel.h` | Keep the three tabs, drawings, remapping, sensitivity, language, version footer and removed contribution/star actions. Add upstream persistence callbacks and the playtime overlay choices, including Japanese. Wait for BOTW patches before evaluating saved output modes. | Panel conflict; prevent dropping BOTW 1.6.0's saved native resolution before its canvas becomes available |
| `games/totk/runtime/frontend.m` | Add playtime accounting and display while keeping version/commit information in the settings footer. Retain the owner's language and modifier-key handling. | Overlay conflict |
| `games/totk/app/launcher.m` | Load the saved interface language before the newly introduced update notice. | Stored Chinese/Japanese choice applies to the new startup dialog |
| `games/totk/app/update_notice.h`, `games/totk/runtime/playtime.h` | Give the new host text explicit Japanese translations through `TOTK_UI3`. | Preserve the owner's three-language interface |
| `tests/settings_panel_probe.m` | Combine the persistence fixture with the remapping/controller/sensitivity fixture. Exercise the supported MetalFX mode on BOTW 1.9.0 and native 2K on the other tested versions. Keep the pre-patch restore assertion. | Probe conflicts; version-specific resolution support |
| `tests/test_settings_panel.py` | Retain upstream save/restore, environment-override, frame-lock and malformed-setting scenarios for all four panel variants. | Persistence regression coverage |
| `games/totk/tests/playtime/probe.m`, `tests/test_ui_language.py` | Check Japanese playtime rendering and include the new host-text files in the existing translation coverage scan. | Language integration |
| `docs/controls.md`, `docs/controls.zh-CN.md` | Preserve the custom keyboard and panel documentation; describe playtime and saved graphics choices. | Documentation conflict and automatically merged text |
| Other upstream files | Keep the snapshot's runtime, graphics, shader lists, tests, build metadata and license changes. | Integrate the requested local main snapshot |

## 4. Verification

Run and passed:

- `build/totk-1.4.3/work/venv/bin/python -m unittest tests.test_settings_panel tests.test_ui_language -q`: 2 tests, including real panel variants for TOTK base/1.4.3 and BOTW 1.6.0/1.9.0, both HUD layouts, remapping/drawings and persistence scenarios.
- Native `playtime` probe, including Japanese text; native `update_notice` probe with fake network responses and temporary state.
- Runtime links using the merged sources in `build/totk-1.4.3/work/totk` and `build/botw-1.9.0/work/totk`: `make -j6 build/totk-native-v143` and `make -j6 build/totk-native-botw190`. Runtime sources use the existing `-Werror` configuration.
- Both game launchers compiled with `-Wall -Wextra -Werror` from the final merged launcher source.

- Full `make check PYTHON=<repository>/build/totk-1.4.3/work/venv/bin/python`: passed. Python ran 469 tests in 120.125 seconds, with 5 skipped; the three UBSan C suites (RomFS paths, controller mapping, keyboard mapping) also passed. The Python run emitted non-fatal subprocess `ResourceWarning` messages.

Initial failures and resolution:

- The sandboxed panel run had no usable screen geometry (expected window height was negative). The window-service-enabled rerun removed that environment failure.
- Persistence testing then exposed BOTW's early output-mode advertisement. The restore readiness guard and version-aware probe described above fixed it; the final targeted run passed.

Logs and standalone probe binaries are local and ignored under `build/records/merge-main-20261028/`.

Not built or tested:

- Complete game apps and DMGs were not rebuilt or repackaged. Existing deliverables do not gain these changes through a source merge.
- No game was played, no gameplay performance or experimental temporal-upscaling image quality was measured, and no installed app or user save was changed.
- No iOS build or device testing; no other game versions or community ports were built.

AI disclosure: merge resolutions, integration adjustments, translations, test adaptations and this record were generated by Codex and verified as listed. They have not been manually tested in gameplay.

## 5. Open items

- Rebuild the apps and DMGs separately when requested to try the merged changes in-game.
- The merge remains local; no network fetch, push or pull request is part of this request.
