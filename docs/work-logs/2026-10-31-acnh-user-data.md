# ACNH user Library data paths

## Request

The owner's request, quoted verbatim:

> 实际的游戏数据不应该存在这里，应该优化一下吧，程序是这么写的吗？

The preceding question identified `/Applications/Animal Crossing Data`. Inspection
confirmed that both the native launcher and packager intentionally used a sibling
directory. This task improves that behavior on `acnh`, with AI assistance from
Codex. Related [self-review](../code-reviews/2026-10-31-acnh-user-data.md).

## Implementation

- Added the native Foundation-based `scripts/acnh_user_data.m` helper and C header.
  The default game-version-specific paths for 3.0.1 are:
  - Persistent data: `~/Library/Application Support/com.nintendo.acnh.native/3.0.1/`.
  - Shader cache and integrity proofs: `~/Library/Caches/com.nintendo.acnh.native/3.0.1/`.
  - Runtime logs: `~/Library/Logs/com.nintendo.acnh.native/3.0.1/`.
- Foundation resolves the normal user-domain directories. Tests inject an
  isolated home path directly into the helper without changing `HOME`.
  This follows Apple's [Library directory guidance](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/MacOSXDirectories/MacOSXDirectories.html).
- Kept save files, account identity, settings, save backups, screenshots, command
  file and game lock in the persistent directory. Cache/proof paths and log
  rotation now use their corresponding Library directories.
- First-launch migration considers the older directory adjacent to that App,
  verifies the version and game lock, and never merges into existing new data.
  Same-volume moves are atomic/exclusive. Copy fallback hashes every regular
  file before publishing and retains the original. Unknown/different save
  versions, links, special files and active games block migration safely.
- Preserved the absolute `ACNH_DATA_DIR` override with the old self-contained
  layout, bypassing default migration for diagnostics.
- Added `--prepare-data` to perform setup/migration without running the game.
  `--check` remains read-only. Packaging no longer creates sibling user data or
  seeds the owner's saves/cache into a package. The launcher is compiled for
  the selected game version; the receipt records the new helper/header identities.
- Updated the README and added native regressions for save preservation,
  preferences/backups/screenshots, version isolation, cache/log separation,
  existing targets, active locks, symlinks, overrides, cross-volume copying,
  interrupted publication/retry, and real launcher environment/log integration.

## Actual validation

- Targeted native user-data and packaging suite: **18 tests passed**.
- Full ACNH unittest discovery: **62 tests passed**, 7.942 seconds; retained in
  `build/acnh-3.0.1/work/logs/acnh-user-data-tests.log`.
- Clang static analysis of `acnh_user_data.m`: exit 0, no diagnostics.
- `git diff --check`: passed.
- Current-source host rebuild with the remembered checked FPS/DLC inputs:
  exit 0, using `MACOSX_DEPLOYMENT_TARGET=27.0`, the verified preparation,
  work-local Python/tools/objects and existing shader caches/seed.
- Final App packaging: exit 0, preserving the verified 3.0.1 game/FPS/three-DLC
  inputs and shader seed. The package contains the new launcher/helper source
  identities and `MNGDataLayoutVersion=1` / `MNGDataDirectoryVersion=3.0.1`.
- Final build metadata: source
  `aa2586849eb113da4175ec51e4911c2f6e422b7a-dirty`, game 3.0.1, minimum macOS
  27.0; `vtool` confirmed deployment 27.0 for both launcher and native runtime.
- Bundled launcher `--check` passed without creating its test data directory;
  `--prepare-data` passed with an isolated override without launching gameplay.
- Bundled native loader probes passed in both 30 and 60 FPS modes. DLC, RomFS
  and constructor/`nnMain` startup probes also passed. The startup probe stops
  at graphics initialization and does not establish gameplay correctness.
- `codesign --verify --deep --strict` passed after the probes. The sandboxed
  packager's nonfatal Launch Services scan error was separate from these checks.
- Detailed build evidence:
  `build/acnh-3.0.1/work/user-data-migration/build-validation.json` and `validation/`.

## Live data and scope

During initial implementation, the installed 3.0.1 game held
`/Applications/Animal Crossing Data/game-slot/lock`.
It was not stopped or migrated during that phase. An ignored snapshot of 17
persistent account/save/preference file identities was recorded under
`build/acnh-3.0.1/work/user-data-migration/owner-before.json`; the running game can
continue writing its own progress, so no whole-session unchanged-save claim is made.

The initial build/test phase only updated the App under `build/acnh-3.0.1/`.
The owner's subsequent explicit migration request authorized updating the
installed launcher and migrating live data, as recorded below. The existing
DMG remains unchanged. Starting an uninstalled build copy normally considers
that build copy's own adjacent legacy directory; tests used an explicit
isolated override to avoid either live profile.

No commit, push, PR or DMG was requested. The pre-existing untracked work logs
remain untouched. The game remains experimental; synthetic migration and loader
checks do not establish full gameplay compatibility.

## Follow-up: owner requested migration

The owner then said, quoted verbatim:

> 我已经结束游戏了，顺便帮我迁移一下存档

The legacy game lock was rechecked and was free. Recorded a new post-quit snapshot
of the 17 persistent save/account/preference files and made local APFS copies of
the complete legacy data directory and installed App under
`build/acnh-3.0.1/work/user-data-migration/before-installed-update/`.
This supersedes the earlier snapshot taken while the game was active.

The requested migration also required replacing the installed launcher so future
launches continue using the new directories. The installed update ran after all
package checks and backups, with the required approval to write outside the
workspace sandbox.

### Installed update and real migration results

- Rechecked the idle legacy game lock and post-quit file identities. Created an
  App staging copy under `/Applications/` and passed strict signature verification
  before replacement. The original installed App was moved into the ignored
  `before-installed-update/Original installed app.app` backup location.
- Replaced `/Applications/Animal Crossing New Horizons.app` with the verified
  new build, then ran its `--prepare-data` without a diagnostic override.
- Migration completed via same-volume atomic relocation. The former
  `/Applications/Animal Crossing Data` no longer exists. Persistent data,
  shader cache/proofs and logs are in the three Library paths listed above.
- **All 27,854 original files** were compared against the complete backup at their
  corresponding new locations, including saves, account, backups, screenshots,
  preferences, shader cache, logs and proofs. Sizes and full SHA-256 hashes match.
  All **17** post-quit persistent save/account/preference identities also match.
- Repeated installed `--prepare-data`: passed, with no recreation of the old
  Applications data folder. Installed launcher `--check`, both 30/60 loader
  probes and final `codesign --verify --deep --strict`: all exited 0.
- Launch Services registration of the installed App: exit 0. No game GUI or
  gameplay was launched, and no save conversion or patching was performed.
- Machine-readable results and detailed logs:
  `build/acnh-3.0.1/work/user-data-migration/installed-validation.json` and
  `installed-*.log`. Full rollback copies remain under `before-installed-update/`.

The migration is complete. The owner can launch the installed App normally and
continue the same island. Source/tests/records were uncommitted at delivery;
the local backups, saves and built App are ignored and must not enter a commit.

## Follow-up: local commit

The owner's request, quoted verbatim:

> 提交commit

This authorizes a local commit on `acnh` of the user-data directory/migration
implementation, packaging integration, tests, README, review and the current
[DMG refresh record](2026-10-31-acnh-dmg-repack.md). Author and committer use
`Sqhh99 <sqhh99@gmail.com>`. The pre-existing unrelated/untracked work logs,
game inputs, migrated saves, rollback copies, App, DMGs and checksums remain
outside the commit. No push or PR was requested.

The 62-test results and completed package, installed migration and mounted DMG
checks were rechecked; no implementation changed after those validations. This
commit step only updates records and Git metadata. It does not rebuild the App
or regenerate the DMG, whose recorded source revision remains the pre-commit
`aa2586849eb113da4175ec51e4911c2f6e422b7a-dirty` described above.
