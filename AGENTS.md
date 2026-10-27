# Repository Contribution Policy

These instructions apply to the entire repository and to all agents working in it.

## Branch roles

- `main` is reserved for synchronizing code from `upstream/main`.
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
- Synchronize `main` from `upstream/main` without adding personal changes.
- Bring upstream updates into `sqhh99` separately, preserving the owner's changes.

## Commit hygiene

- Use `Sqhh99 <sqhh99@gmail.com>` for the owner's commits.
- Stage only files relevant to the requested change. Do not include downloaded game files, key archives, credentials, saves, or build artifacts.
