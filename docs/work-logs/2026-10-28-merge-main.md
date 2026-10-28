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

- The TOTK app was subsequently rebuilt as recorded below. The BOTW app and both DMGs still need a separate rebuild to include this merge.
- The merge remains local; no network fetch, push or pull request is part of this request.

## 6. Follow-up: build the TOTK app for the owner's test

> APP构建了吗？构建一下王国之泪的app，我运行测试一下

Built the complete Mac app from `sqhh99` at `ef68d118751861d1667a3282f698b91fd1f879c6` using `python3.14 build/build_game.py totk-1.4.3`. The helper passes explicit `--work build/totk-1.4.3/work` and `-o "build/totk-1.4.3/Tears of the Kingdom.app"` paths and selects the base XCI, separate 1.4.3 update NSZ, shared fonts and shared keys under `game-assets/`. It reuses verified extracted game data and build caches. No source code changed for this build.

- **App:** `build/totk-1.4.3/Tears of the Kingdom.app`.
- **Build:** completed successfully in 211.5 seconds. Both the short and full source revision are recorded in the app's Info.plist.
- **Shader seed:** 31,307 prepared variants. The seed generator skipped 84 translation candidates; its reuse/build behavior allows these skips. The Mac GPU warm-up compiled all 31,307 prepared variants with zero failures in 174.6 seconds, and a separate process found all 64 sampled cache entries.
- **Final validation:** set `LSMinimumSystemVersion` to `27.0` to match the actual local deployment target, ad-hoc re-signed the app, passed strict signature verification and launcher `--check`, and passed the runtime loader's cross-module probe against the bundled game modules. The probe also exercised installation of the new high-FPS fade patch without running game entry code. No key files are bundled.
- **Records:** `build/totk-1.4.3/build-status.json`, `build.log`, `app-validation.json` and `work/logs/`.
- **Source checks:** not rerun for this artifact-only follow-up; the same source commit passed the checks in section 4.
- **Not done:** no DMG packaging, installation, gameplay test or changes to the owner's saves. BOTW was not rebuilt. Moving the app can require shader warm-up again at its new location.

AI disclosure: Codex ran the existing build helper, adjusted the artifact's minimum-system declaration, ran validation and wrote this record. The owner will perform gameplay testing.

## 7. Follow-up: document the incremental build workflow

> 我发现你的构建方法很快，把它整理到AGENTS.md和CLAUDE.md去

Plan: compare the successful build invocation with the builder and existing guidance, document the reusable workflow in English, and check the new command examples without rerunning the build.

| File | Change |
|---|---|
| `AGENTS.md` | Add the canonical incremental Mac app workflow: preserve per-version work/cache/venv data; use the full builder for app requests; list local wrapper commands and equivalent explicit commands for both games; retain integrity checks and source synchronization; validate revision, minimum macOS, signature, launcher and bundled-module loading; distinguish apps from DMGs and installation. |
| `CLAUDE.md` | Link to the canonical workflow, add quick commands and venv-based source checks, and replace the blanket build-duration estimate with cold/warm build guidance backed by the measured TOTK build. |
| This work log | Record the documentation request and verification while retaining the preceding app-build record. |

Verification: compared the instructions with `build/build_game.py`, `build_app.py`, `update_runtime.probe_runtime` and the successful build records. All five new shell code blocks passed `sh -n`; all eight referenced local input files/directories exist. `git diff --check` passed. No source code changed; no game build, `make check`, gameplay, packaging, installation, commit or push was performed for this documentation follow-up. Earlier build/test results remain historical results, not newly rerun checks.

AI disclosure: Codex wrote the documentation and checked it as listed. The local wrapper remains ignored; complete commands are included so a fresh checkout does not depend on that file.

## 8. Follow-up: commit the build documentation

> 提交commit

Commit scope: `AGENTS.md`, `CLAUDE.md` and this work log, including the preceding app-build and documentation records. Keep the commit on `sqhh99` with identity `Sqhh99 <sqhh99@gmail.com>`; do not push. Check the diff and staged file list before committing. This is a documentation-only commit; no new build or test-suite run is needed, and section 7 records the command-example checks already performed.
