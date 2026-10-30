# ACNH 3.0.1 60 FPS and DLC commits review

AI-assisted review by Claude Code (Claude Opus 5.5) on 2026-10-30 of `323d131`
(selectable 30/60 FPS) and `1b52cf7` (three pinned DLCs). No independent human
reviewer was used. The follow-up changes and their validation are in the
[work log](../work-logs/2026-10-30-acnh-fps-dlc-optimizations.md). Earlier records:
[60 FPS work log](../work-logs/2026-10-29-acnh-60fps.md),
[DLC work log](../work-logs/2026-10-29-acnh-dlc.md),
[DLC self-review](2026-10-29-acnh-dlc.md).

## Independent check

All 6,417 SpeedFix replacement words were classified against the instruction
rewriter's rules (`third_party/d2r/patch_nso.py`) using the local prepared 3.0.1
data. None is an `svc`, a `tpidr`/`tpidrro`/`cntpct`/`cntvct` access or an x18
use; none of the 974 branches targets a rewritten word or leaves the text
segment. 6,334 sites are in text, 43 in read-only data and 40 in data. One site
(`main+0x1e54474`) is two words after an x18 gate at `main+0x1e5446c`; that gate
block returns to `+0x1e54470`, so the corrected word still executes.

## Findings and disposition

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | `runtime_present_interval()` raised intervals below 2 to 2 in every 3.0.1 build, including builds without FPS data, contrary to the README's "original timing" claim | Medium | Fixed: the 30 FPS lock applies only when the selector is available (FPS data present) |
| 2 | `prepare_fps.py` checked original words but not replacement words against the rewriter's gated classes | Low | Fixed: `check_replacement()` rejects gated svc/system-register words, x18 use and branches out of text or into rewritten code; unit test added |
| 3 | `build_host.py` remembered `--fps-mod`/`--dlc` with no way to drop them | Low | Fixed: `--no-fps-mod` and `--no-dlc` |
| 4 | `prepare_dlc.py` required all three pinned packages | Medium | Fixed: any non-empty subset in pinned order; unit test added |
| 5 | Each launch rehashed the 623 MB Happy Home Paradise image | Low | Fixed: per-image verification record in `TOTK_ROMFS_PROOF_DIR`, same identity rules as the base RomFS; `TOTK_ROMFS_VERIFY=full` forces a hash; test added |
| 6 | OLSC command 14 bundled into the FPS commit; enabling backup returns kernel-module `0xd401` | Low | Not changed: the correct OLSC result is unverified, and splitting the commit would rewrite local history |
| 7 | `ACNH_DLC_DEFAULT_DIR` embeds an absolute local path | Low | Not changed: the runtime already embeds seven local paths from debug information; the launcher always sets `ACNH_DLC_DIR` |
| 8 | Missing or changed DLC image stops every launch | Design | Kept deliberately (fail closed rather than hide content a save may need); documented |
| 9 | Policy: in-memory checked patching of `main` from CC BY-NC data | Note | Consistent with the existing checked runtime patches (`acnh_ctx_lock.c`, `acnh_ui_patch.c`); keep it out of upstream PR #1305 and shared builds |
| 10 | Gameplay coverage: one outdoor 60 FPS scene; no DLC gameplay | Risk | Unchanged; still requires play testing with backed-up saves |

The DLC lock order (host fs lock, then DLC lock), bounded read-only slices,
traversal rejection, mount-name collision checks and coverage of all four
AddOnContent imports used by 3.0.1 `main` were confirmed correct.
