# ACNH: sync acnh with main and open the 3.0.1 FPS/DLC pull request

## User request

> I have just pulled the latest code from the remote `main` branch, which is now up to date with the original repository. Could you please sync the `acnh` branch with this latest `main` branch code and submit a pull request (PR)? This update—targeted for version 3.0.1—includes support for 60 FPS and compatibility with the DLC.

AI assistance: Claude Code (Claude Opus 5.5). PR record:
[2026-10-30-acnh-fps-dlc](../pull-requests/2026-10-30-acnh-fps-dlc.md).

## Sync

- `main`, `origin/main` and `upstream/main` were all `933b6a0`. That includes
  #1305 (merged as `d6e8f91` from `feat/acnh-3.0.1` at `1f193c6`) and the
  maintainer's comment-only follow-up `8c7c2eb`.
- A plain merge of `main` into `acnh` conflicted on most `games/acnh` files. The
  cause: #1305 carried `acnh`'s work as separately created commits with identical
  `games/acnh` content (`git diff f7f4473 1f193c6` over `games/acnh`, `README.md`
  and `.gitignore` is empty). That merge attempt was aborted.
- First, the feature branch `feat/acnh-3.0.1-fps-dlc` was created from `main`. The
  three new commits were applied to it without their `docs/` records:
  - `02c5f0a` from `323d131`;
  - `3290424` from `1b52cf7`;
  - `123739c` from `0a67bfa`.
  Their messages now point to the records on the fork's `acnh` branch.
- Its `games/acnh` differs from `acnh` at `0a67bfa` only by `8c7c2eb`'s lines
  (checked with a diff).
- Merge `3a22ad1` (`acnh` + `main`): its tree is the feature branch plus `acnh`'s
  own `AGENTS.md`, `CLAUDE.md`, `docs/work-logs`, `docs/code-reviews` and
  `docs/pull-requests` files, unchanged from `0a67bfa`. Everything else follows
  `main`.

## Actual validation (at `3a22ad1`)

- **ACNH suite:** 51 tests passed.
- **Root `make check`:** passed (exit 0): 1,302 tests OK, 169 skipped, followed by
  the C checks. The two `tests/test_builder_mod_archive.py` errors recorded in the
  [follow-up log](2026-10-30-acnh-fps-dlc-optimizations.md) no longer occur on
  this `main`.
- **Rebuild:** `build_host.py` rebuilt the runtime with the remembered FPS and DLC
  inputs (exit 0, `work/logs/host-sync-main.log`).
- **Repackage:** `package_native_app.py` repackaged
  `build/acnh-3.0.1/Animal Crossing New Horizons.app` (exit 0,
  `work/logs/package-sync-main.log`). Source revision `3a22ad1…` (not dirty).
- **Packaged checks:** all passed.
  - Version 3.0.1; deployment target 27.0 in `LSMinimumSystemVersion` and in the
    Mach-O `minos` of the runtime and the launcher.
  - FPS bundle and adapter identity (manifest `8bc14228…`).
  - DLC identity (3 DLCs, `7fdb92da…`).
  - Bundled loader `probe` at 30 FPS (no corrections) and at 60 FPS (6,417
    installed).
  - `probe-dlc` three times (1,173 files, 622,961,944 bytes): full hash, record
    reused, forced full hash.
  - Launcher `--check` and `codesign --verify --deep --strict`.
  - The owner's 11 save files were unchanged by the checks.
- **Gameplay:** not run in this session. The PR cites the owner's earlier session
  of about 60 minutes at 60 FPS (recorded in the follow-up log). That session's
  log also shows all three DLCs verified and mounted. No DLC-specific content was
  confirmed played, and 1.2.1 was not rebuilt.

## Publishing

`acnh` and `feat/acnh-3.0.1-fps-dlc` were pushed to `origin`. The PR was opened
against `ly05010419/MacNativeGames` `main` as [#1393](https://github.com/ly05010419/MacNativeGames/pull/1393) (verified open and mergeable; details in the PR
record). No DMG was made and nothing was installed outside `build/`. The three
untracked work logs from 2026-10-28/29 were left untouched.
