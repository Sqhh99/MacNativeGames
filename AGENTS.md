# Repository Contribution Policy

These instructions apply to the entire repository and to all agents working in it.

## Branch roles

- `main` is a local upstream reference snapshot, not the active development branch.
- Do not commit personal code, documentation, tests, or configuration changes to `main`.
- Do not merge personal branches into `main`.
- `sqhh99` is the long-lived branch for the owner's changes.
- Start new personal work on `sqhh99`, or create a feature branch from the latest `sqhh99`.

## Pull request destination

- All pull requests for personal changes must target `sqhh99`.
- Never create or retarget a pull request to `main` in the owner's repository or any fork used for this project.
- Use an explicit repository and base branch when creating or updating a pull request. For this fork:

  ```sh
  gh pr create --repo Sqhh99/MacNativeGames --base sqhh99 --head <feature-branch>
  gh pr edit <number> --repo Sqhh99/MacNativeGames --base sqhh99
  ```

- Verify the resulting pull request's repository and base branch after submitting it.
- If `sqhh99` does not exist on the destination remote, create it before opening the pull request. Never fall back to `main`.
- Keep existing personal-change pull requests pointed at `sqhh99` as well.

## Upstream synchronization

- `upstream` is the original project; `origin` is the owner's fork.
- Do not fetch or pull `upstream/main` unless the owner explicitly requests a new upstream update.
- Do not push `main` to `origin` unless the owner explicitly requests it. The remote `main` may remain older than the local snapshot.
- When asked to merge `main` into `sqhh99`, use the existing local `main` without refreshing it from the network.
- Preserve the owner's changes when merging that snapshot into `sqhh99`.

## Commit hygiene

- Use `Sqhh99 <sqhh99@gmail.com>` for the owner's commits.
- Stage only files relevant to the requested change. Do not include downloaded game files, key archives, credentials, saves, or build artifacts.

## Project records

- Follow `agents/skills/project-records/SKILL.md`: a work log in `docs/work-logs/` after any request that changes files, a review archive in `docs/code-reviews/` after a code review, and a PR record in `docs/pull-requests/` before opening a pull request.
- Never mark a check as passed unless it was run.

## Local game assets

- Keep local inputs under `game-assets/`, excluded from Git.
- Use ASCII English directory and file names. Organize each game by purpose and then version, such as `breath-of-the-wild/updates/v1.9.0/`.
- Keep base packages, combined images, separate updates, DLC, mods, cheats, and guides in their respective categories. Retain older versions without overwriting them.
- Keep shared fonts in `game-assets/shared/fonts/`, preserving the filenames required by the build tools.
- Keep one shared key archive at `game-assets/shared/keys/switch-keys-v22.5.0.zip`. The three original archives were verified byte-for-byte identical and the keys were checked against both games; do not recreate per-game copies.
- Preserve the asset manifest's original-path mappings and content hashes. Do not print key values or commit the asset library.
- Keep mods and cheats with unconfirmed compatibility under `unknown`; do not install or enable them as part of an ordinary build.

## Build layout and selected versions

- Put all game builds under the repository's `build/<game>-<version>/` directory, using the game abbreviations `botw` and `totk`.
- Use `build/botw-1.9.0/` and `build/totk-1.4.3/` for the currently requested builds. Do not use an extra game/version nesting level.
- Place each version's work folder at `<build-directory>/work/`, and its final app and DMG directly in `<build-directory>/`.
- Always pass explicit `--work` and `-o` paths to the build scripts so their legacy defaults do not create `BotW_build/` or `TOTK_build/` again.
- The owner requested removal of the old root-level `BotW_build/` and `TOTK_build/`. Preserve small integrity and migration records under `build/records/` before cleanup; do not remove game inputs, installed applications, or the user's saves.
- Build BOTW 1.9.0 from its base NSP, separate 1.9.0 update NSP, both DLC NSPs, shared fonts, and the shared keys.
- Build TOTK 1.4.3 from its base XCI, separate 1.4.3 update NSZ, shared fonts, and the shared keys.
- Include the owner's existing settings-panel customization in personal builds: remove the shader/pipeline contribution and project-star actions, and keep suitable footer spacing while preserving supported upstream controls.
- Validate each completed app before packaging its DMG. Keep final deliverables in the build directory unless the owner explicitly requests installation.

## Incremental Mac app builds

- For an ordinary source update, rebuild with the existing version's work folder. Preserve extracted/rewritten game data, the work-local `venv`, pinned tools, object files, translated shader seeds and Metal caches. Do not clean or recreate these folders merely because a branch was merged.
- Let `build_app.py` check recorded inputs and hashes and rebuild invalidated stages. Never skip integrity checks or force stale data to match. Verified reuse must preserve the app assembly and validation stages.
- Use the full app builder for the normal "build the app so I can test it" request. Compiling `totk-native-*` alone does not update the app. Build only the requested game; package a DMG or install into Applications only when requested.

From the repository root, the existing local wrappers provide the selected inputs, explicit work/output paths, macOS deployment target and build logs:

```sh
python3.14 build/build_game.py totk-1.4.3
python3.14 build/build_game.py botw-1.9.0
```

Run the command for the requested game, not both by default. These wrappers are git-ignored local conveniences; a fresh checkout may not have them. The equivalent full commands are:

```sh
MACOSX_DEPLOYMENT_TARGET=27.0 python3.14 build_app.py \
  game-assets/tears-of-the-kingdom/base/v0/totk-base-v0-0100f2c0115b6000.xci \
  --update game-assets/tears-of-the-kingdom/updates/v1.4.3/totk-update-v1.4.3-0100f2c0115b6800.nsz \
  -k game-assets/shared/keys/prod.keys --shared-fonts game-assets/shared/fonts \
  --work build/totk-1.4.3/work -o "build/totk-1.4.3/Tears of the Kingdom.app"

MACOSX_DEPLOYMENT_TARGET=27.0 python3.14 build_app.py \
  game-assets/breath-of-the-wild/base/v0/botw-base-v0-01007ef00011e000.nsp \
  --update game-assets/breath-of-the-wild/updates/v1.9.0/botw-update-v1.9.0-01007ef00011e800.nsp \
  --dlc game-assets/breath-of-the-wild/dlc/botw-dlc-01007ef00011f001.nsp \
  --dlc game-assets/breath-of-the-wild/dlc/botw-dlc-01007ef00011f002.nsp \
  -k game-assets/shared/keys/prod.keys --shared-fonts game-assets/shared/fonts \
  --work build/botw-1.9.0/work -o "build/botw-1.9.0/Breath of the Wild.app"
```

- The builder synchronizes current sources into `work/totk/` using content comparison and rebuild-safe timestamps. Do not run `make` against an old work-tree source copy and assume it includes the current checkout.
- Reuse the build's Python environment for source checks when dependencies are already installed, for example `make check PYTHON="$PWD/build/totk-1.4.3/work/venv/bin/python"`. Do not reinstall the same dependencies globally for each build.
- A warm TOTK 1.4.3 rebuild at `ef68d11` took 211.5 seconds on this Mac on 2026-10-28, including 174.6 seconds of Metal warm-up. This is an observed cached build, not a promised duration: first builds, changed inputs/translators and cold GPU caches can take much longer.
- Let the builder finish shader preparation and warm-up. Missing optional offline Metal tooling is handled by warming the Mac's Metal cache. Report actual compiler failures, allowed seed-generator skips, and any skipped warm-up separately. Moving the app can make the cache cold again; wait for startup warm-up before gameplay testing. Do not quit unrelated apps to obtain the cache without authorization.

Before handing over an app:

1. Confirm the build exited successfully and the app's `CFBundleShortVersionString`, `MNGSourceCommit` and `MNGSourceRevision` identify the intended version and checkout. Local wrappers record status in `build-status.json` and output in `build.log`; stage logs are in `work/logs/`.
2. Ensure `LSMinimumSystemVersion` matches the actual binary/dependency deployment target. These local commands target macOS 27; the upstream template may still declare 26. If the plist needs correction, ad-hoc re-sign the app with `codesign --force --sign - "<app>"` before the final checks.
3. Run `codesign --verify --strict "<app>"` and the app's `Contents/MacOS/<CFBundleExecutable> --check`. For the current TOTK app, that executable is `Contents/MacOS/TOTK`.
4. Run the native loader probe against the bundled modules. It checks their hashes and cross-module calls without starting gameplay, constructors, a game window or GPU work. For TOTK:

   ```sh
   python3.14 - <<'PY'
   from pathlib import Path
   from update_runtime import probe_runtime
   probe_runtime(Path("build/totk-1.4.3/Tears of the Kingdom.app").resolve(), "v143",
                 Path("build/totk-1.4.3/work/logs").resolve())
   PY
   ```

   For BOTW use its app/log paths and version identifier `botw190`.
5. Record the results in the work log and provide the final app path. Distinguish build/probe success from actual gameplay testing. An existing DMG still contains its older app until explicitly repackaged.

For a narrowly scoped runtime/launcher-only update, `update_runtime.py` is an alternative when the existing app has complete matching game data. Always pass its version's explicit `--work` path; use `--seed` when the startup seed must be regenerated. This path can reuse the app's bundled game data without the original packages/keys; the full builder commands above still select them. Never treat this shortcut as a way to reuse mismatched game versions or skip validation.
