# ACNH user-data location and migration review

AI-assisted self-review by Codex, 2026-10-31. No independent reviewer was used.
Related [request and validation log](../work-logs/2026-10-31-acnh-user-data.md).

## Scope and decisions

- Replaced the App-adjacent default with version-isolated user Library paths.
  Persistent saves/settings/backups remain together; shader caches and verification
  proofs use Caches, and the two runtime logs use Logs.
- Removed profile/cache seeding from packaging. A build and `--check` must not
  initialize or migrate the user's live profile.
- Preserved the explicit `ACNH_DATA_DIR` override for isolated diagnostics and
  portable use, with no automatic migration in that mode.
- Reviewed launcher integration: profile, controls, screenshots/working directory,
  shader cache, proofs, log rotation and automatic save backup follow the resolved
  paths. The signed bundle is never a writable data root.

## Migration checks

- Migration takes a version-specific setup lock and checks the older game's
  live slot lock before touching its directory. It never stops a running game.
- Existing destination data is authoritative; source data is never merged into
  it. Known different/unknown legacy save versions are rejected, and version
  strings cannot contain directory traversal components.
- Same-volume relocation publishes via an exclusive atomic rename. Cross-volume
  or read-only-source fallback copies to a private staging directory, compares
  every regular file's size/SHA-256 with both source snapshots, then publishes
  via exclusive rename and preserves the original source.
- Links and special files in a legacy tree are rejected. Failed publication
  removes only the new staging directory, leaving the original save intact.
- Cache/log reorganization can resume on a subsequent launch after interruption.
  A destination already containing a cache or log file is never overwritten by
  the migration helper.

No blocking issue was identified in this self-review. Native migration tests
cover the failure/compatibility cases, including injected cross-volume and
publication failures. Clang static analysis completed without diagnostics.
Initial tests ran while the installed game was still running. After the owner
quit and explicitly requested migration, the installed App was updated and the
real migration completed; all 27,854 original files matched their full backup
at the new locations. Installed signature/loader checks also passed. No new
GUI/gameplay validation is claimed.
