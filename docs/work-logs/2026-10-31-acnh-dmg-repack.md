# ACNH 3.0.1 DMG refresh after user-data migration

## Request

The owner's request, quoted verbatim:

> 帮我重新打包一下

AI assistance: Codex. Related record:
[user Library paths and actual save migration](2026-10-31-acnh-user-data.md).
The previous DMG's pre-existing local record,
`docs/work-logs/2026-10-30-acnh-3.0.1-dmg.md`, remains untracked and is not included
in the subsequent commit of this task's changes.

## Source and scope

Reused the current verified App at
`build/acnh-3.0.1/Animal Crossing New Horizons.app`:

- Game 3.0.1, three DLCs and the existing optional 30/60 FPS data.
- Source revision `aa2586849eb113da4175ec51e4911c2f6e422b7a-dirty`.
- `MNGDataLayoutVersion=1`, `MNGDataDirectoryVersion=3.0.1`, minimum macOS 27.0.
- App receipt built at `2026-10-31T13:56:42Z`; its launcher/helper/header hashes
  matched current sources before staging. The earlier 62-test and package/installed
  validation results remain in the user-data work log; no unnecessary rebuild
  or repeated unit-test run was performed for this packaging-only task.

The staging folder contains only an APFS-cloned App and the `/Applications`
installation link. No save, user profile, settings, backup, screenshot, runtime
log or writable shader-cache directory is included. Bundled game resources and
the offline shader seed remain part of the App.

The image uses the previous APFS/ULFO format and volume name
`Animal Crossing New Horizons`. The old DMG remains in place until the new image
has passed verification; it is then preserved under the ignored work directory
and the new image is published by rename at the normal output path, with rollback
if publication fails.

## Actual validation

- Source App strict signature and launcher `--check`: passed before staging.
- Initial sandboxed `hdiutil create`: failed with `Device not configured`;
  no output image was produced. The system image workflow was rerun with the
  required outside-sandbox permission. The tool also emits a deprecation notice
  for `hdiutil create`; this is recorded in its log.
- Image creation and `hdiutil verify`: passed. The image's CRC32 verification
  reported `VALID`.
- Mounted read-only at an explicit work-local mountpoint. Strict App signature,
  launcher `--check`, native loader probes in both 30 and 60 FPS modes, and the
  three-DLC probe: all exited 0. The launcher check created no user-data folder.
- Mounted metadata matched the source exactly: game 3.0.1, source revision above,
  user-data layout 1, data version 3.0.1 and three DLC entries. Both Mach-O files
  reported minimum deployment macOS 27.0.
- Compared all **22,360 regular files** by full SHA-256 and size, plus directory
  entries and literal symbolic-link targets (**22,383 entries** total), against
  the verified source App. Everything matched, including the entire shader seed.
- The image root contains only the App and Applications link apart from filesystem
  metadata. No legacy `Animal Crossing Data`, profile or save directory was found.
- Detached successfully, preserved the previous DMG, published the new image and
  wrote its SHA-256 sidecar. The temporary staging clone was removed.

## Final output

- DMG: `build/acnh-3.0.1/acnh-3.0.1-arm64-macOS27.dmg`.
- Size: **10,939,007,949 bytes**.
- SHA-256: `5a459c59e80b6128c42f104cf6c075222e1fd55d4882b0a9f62a2cdf65872aa0`.
- Checksum: `build/acnh-3.0.1/acnh-3.0.1-arm64-macOS27.dmg.sha256`.
- Previous image retained at
  `build/acnh-3.0.1/work/dmg-repack-2026-10-31/previous-acnh-3.0.1-arm64-macOS27.dmg`.
- Detailed checks, logs and full file manifest are retained under
  `build/acnh-3.0.1/work/dmg-repack-2026-10-31/`, including `validation.json`.
- Completed `2026-10-31T14:15:16Z`.

## Limits and local artifacts

No GUI/gameplay session, App installation, save migration, commit, push or PR
was performed during packaging. The subsequent local commit request is recorded
in the linked user-data work log. The previously installed updated App and migrated
user Library data remain in place. Build/image files, the staging and test
directories, checksum and verification manifests remain ignored local output;
they must not be committed. Pre-existing unrelated work logs were preserved.
