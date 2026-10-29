# ACNH Development Policy

These instructions apply to this repository checkout.

## Branches

- `acnh` is the dedicated branch for Animal Crossing: New Horizons support,
  compatibility fixes, optimization, tests and related documentation.
- The ACNH contribution baseline is the latest requested fork `origin/main`,
  not `sqhh99`. Continue existing ACNH work on `acnh`, or create a feature branch
  from the latest `acnh`. Refresh or rebase its main baseline when the owner asks.
- Keep unrelated `sqhh99` history and other-game customizations out of this branch.
- Do not commit personal changes to `main`, merge this branch into `main`, or
  push `main` without an explicit request. Fetch the fork's main when requested;
  fetching the original project's `upstream/main` is a separate action.
- Publish requested ACNH changes to `origin/acnh` on `Sqhh99/MacNativeGames`.
  The branch is prepared for a future contribution to the original project;
  create a PR only when requested, with an explicit repository and base branch.

## Scope and commit hygiene

- Keep game code, tools and tests self-contained under `games/acnh/`. Do not
  import or read another game's implementation from the ACNH build flow.
- Use `Sqhh99 <sqhh99@gmail.com>` for the owner's commits.
- Stage only relevant source, tests and records. Never commit game packages,
  keys, fonts, saves, rewritten game modules, translated shaders or build output.
- Keep local inputs under ignored `game-assets/`, using ASCII English paths.
  Keep ACNH 3.0.1 output under `build/acnh-3.0.1/`, work under its `work/`, and
  the final app directly in the build directory. Preserve shared input filenames,
  original-path/hash manifests, and unconfirmed mods/cheats without enabling them.

## Builds and validation

- Follow `games/acnh/README.md` and pass explicit work/output paths. Reuse
  verified prepared data, the work-local Python environment, tools, object files
  and shader caches. Rebuild current sources and repackage the app for testing.
- Preserve version pins and integrity checks; never bypass them to accept a dump.
- Check game/source versions, deployment target, strict code signature, launcher
  `--check`, and the bundled native loader probe before handing over an app.
- Run relevant tests and distinguish build/probe success from gameplay testing.
  ACNH 3.0.1 remains experimental until its remaining gameplay/graphics paths are
  verified. Package a DMG or install outside `build/` only when requested.
- Preserve the owner's settings-panel preferences: omit shader/pipeline
  contribution and project-star actions while retaining supported controls.

## Records

- Write an English work log in `docs/work-logs/YYYY-MM-DD-<topic>.md` after file
  changes, quoting the user's request verbatim and recording actual validation.
- Archive code reviews under `docs/code-reviews/`; write a PR record under
  `docs/pull-requests/` before opening a PR. Cross-link related records.
- Never mark a check passed unless it ran. Disclose AI assistance and preserve
  known limitations, skipped checks and local work that was not included.
