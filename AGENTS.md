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
