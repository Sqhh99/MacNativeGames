# Work log: upstream build of `main`, and a PR fixing the ability wheel with the mouse

- **Date:** 2026-10-28
- **Branch:** `fix/ability-wheel-mouse`, from local `main` at `aab06fa`, in the worktree `build/totk-1.4.3-upstream/source`
- **Related:** [PR record](../pull-requests/2026-10-28-ability-wheel-mouse.md), [ly05010419/MacNativeGames#1196](https://github.com/ly05010419/MacNativeGames/pull/1196), [the fixes on sqhh99](2026-10-28-wheel-rotate-arrow-labels.md)

## 1. Request
> Let's build the game on the `main` branch so I can test whether the issues numbered 3 and 4 still exist.

> Issue 3 exists; please submit a PR to fix it. This problem occurs when using a keyboard and mouse.

> Issue 4 was actually caused by me having motion-based aiming enabled; once I turned it off, the problem with the camera shaking erratically while using the mouse disappeared.

> I have tested it, and the issue has been fixed.

Before this, I had claimed that the sqhh99 issues probably existed upstream. On checking upstream `main`:
- **Rotation with Ultrahand:** caused by the sqhh99 layout. Upstream has R on E and the d-pad on F/T/H/G.
- **Arrow-key labels:** caused by the sqhh99 drawing; upstream has none.
- **The wheel (issue 3) and the Ultrahand shaking (issue 4):** the same code upstream, so they had to be checked in a build of `main`.

## 2. Plan
1. Build upstream `main` without touching the sqhh99 app or work folder.
2. The owner tests issues 3 and 4 in that build.
3. For the confirmed issue 3, write a one-topic fix on a branch from `main`, adapted to upstream's code: upstream has no keyboard layout module, only `input.c`'s fixed `keys[]` table.
4. Test the fix, build it, and have the owner try it in game.
5. Push the branch to the fork and open the PR upstream.

## 3. Files changed
### On `fix/ability-wheel-mouse` (commit `2d0f0f0`, the PR)
| File | Change |
|---|---|
| `games/totk/runtime/mouse_look.h` | `mouse_look_point`: pointing while L is held (held, cut to 1, no camera or gyro turn, centred on entry and exit). |
| `games/totk/runtime/gamepad.m` | The mouse tick points while L is held from the keys or a controller (`#ifndef GAME_BOTW`). |
| `games/totk/runtime/input.c`, `runtime.h` | `runtime_keyboard_buttons()`: an atomic, updated whenever `keys[]` changes. |
| `games/totk/tests/mouse_look/probe.c`, `games/totk/tests/mouse/probe.m` | Pointing checks, and an end-to-end check with L held from the keys. |
| `games/totk/tests/{settings_controller,text_keyboard,gamepad_type}/probe.m` | Stub for `runtime_keyboard_buttons`. |
| `docs/controls.md`, `docs/controls.zh-CN.md` | One sentence each in the Mouse section. |

### On `sqhh99` (not committed)
- This work log.
- `docs/pull-requests/2026-10-28-ability-wheel-mouse.md`.

### Local, git-ignored
`build/totk-1.4.3-upstream/` holds:
- `source/`: a git worktree of `main`, now on the PR branch;
- `work/`: an APFS clone of `build/totk-1.4.3/work`, sharing disk blocks;
- the app and the build logs.

## 4. Verification
- **Upstream `main` build:**
  - `build_app.py` from the worktree, with explicit `--work` and `-o` under `build/totk-1.4.3-upstream/`, completed in 17 min. Most of that was the Metal warm-up for the new location: 31,307 shaders in 856 s.
  - The builder's sync had left two sqhh99-only headers (`keyboard_map.h`, `bindings_diagram.h`) in the cloned work copy, because the sync does not delete extra files. Nothing includes them.
  - The runtime contains none of the sqhh99-only strings (`keyboard.txt`, `mouse-sensitivity.txt`, `ui-language.txt`, "Key bindings", 視点); the sqhh99 runtime contains all of them.
  - `LSMinimumSystemVersion` set to 27.0 and re-signed. Strict `codesign`, `--check` and `probe_runtime` pass.
- **Owner's tests on `main`:**
  - Issue 3 reproduces.
  - Issue 4 comes from motion aiming being on; with it off, the shaking is gone. So it was left out of the PR.
- **Branch tests:**
  - The 6 CI C tests pass.
  - `../work/venv/bin/python -m unittest discover -s tests`: 465 tests, OK, 5 skipped.
  - `probe-input`, `probe-input-file` and `probe-autoload` pass, once the ignored `build/` and `analysis/` output folders existed in the fresh worktree.
  - A first run failed `settings_controller`: its stub was inside `command_q`'s `#ifndef FRONTEND_REAL_GAMEPAD`. It was moved to `settings_controller/probe.m`.
  - Compile check (`-Werror -fsyntax-only`) of `frontend.m`, `gamepad.m` and `input.c` for 1.4.3 and BotW 1.9.0 passes.
- **Fix build:**
  - Completed in 2 min (shaders 96 s); `MNGSourceCommit` is `2d0f0f0`.
  - Plist fixed and re-signed; strict `codesign`, `--check` and `probe_runtime` pass.
- **Owner played the fix build** (TOTK 1.4.3, keyboard and mouse): "the issue has been fixed".
- **PR:** pushed `fix/ability-wheel-mouse` to `origin` and opened #1196 on `ly05010419/MacNativeGames`. Verified: open, base `main`, head `Sqhh99:fix/ability-wheel-mouse`, 1 commit, 11 files.
- **Not run:** `--platform ios` (no iOS SDK) and a BotW build. Both are stated in the PR.

## 5. Open items
- **Before merge:** someone with the iOS SDK needs to run the iOS build; the PR says so.
- **Review:** watch #1196 for review comments.
- **Cleanup:** the worktree and `build/totk-1.4.3-upstream/` can be removed (`git worktree remove`) once the PR is settled. The cloned work folder only uses disk where it differs from the original.
- **This log and the PR record:** not committed to `sqhh99` yet.
