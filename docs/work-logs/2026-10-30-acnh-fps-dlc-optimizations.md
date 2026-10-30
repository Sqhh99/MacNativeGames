# ACNH 3.0.1 FPS and DLC review follow-up

## User requests

> Yesterday, I used GPT to help me implement two features, for which I submitted two commits to the `anch` repository: one to add support for a 60 FPS frame rate, and another to enable the loading of three DLCs. Could you please review these implementations and check for any potential issues or risks?

> Please optimize everything for me.

AI assistance: Claude Code (Claude Opus 5.5). Review record:
[code review](../code-reviews/2026-10-30-acnh-fps-dlc.md).

## Changes

Base: `acnh` at `1b52cf7` (two commits ahead of `origin/acnh`), uncommitted.

- `runtime/frame_rate.c`: the 30 FPS presentation lock (interval below 2 raised
  to 2) applies only when the 30/60 selector is available. 3.0.1 builds without
  FPS data, and 1.2.1, keep the game's own interval again.
- `tools/prepare_fps.py`: `check_replacement()` rejects a text-segment
  replacement that is an `svc` or system-register move, uses x18, or branches
  outside the text segment or into rewritten code. The current pinned data
  passes all 6,417 checks.
- `build_host.py`: `--no-fps-mod` and `--no-dlc` drop remembered inputs.
- `tools/prepare_dlc.py`: accepts any non-empty subset of the pinned DLCs, kept
  in pinned order; `verify_assets()` rejects reordered, duplicated or altered rows.
- `runtime/dlc.c`: per-image verification record
  (`.dlc-verified-<title>-v1` in `TOTK_ROMFS_PROOF_DIR`) storing the pinned
  SHA-256 and file identity (device, inode, size, mtime, ctime, birth time),
  reused while unchanged; `TOTK_ROMFS_VERIFY=full` forces a full hash. Without a
  proof directory every launch still hashes in full.
- Tests: unlocked-interval cases, replacement rules, DLC subsets and proof
  reuse/forced/edited cases. README updated.

## Actual validation

- ACNH suite: **51 tests passed** (`unittest discover -s games/acnh/tests`).
- Root `make check`: **failed**, 1,249 tests, 2 errors, 163 skipped. Both errors
  are `tests/test_builder_mod_archive.py` `Stopping.test_a_cancel_kills_tar` and
  `test_a_timeout_kills_tar` (the fake `tar` never writes its pid file). They
  also fail when run alone, inside and outside the sandbox. This change touches
  only `games/acnh/`; the cause was not investigated. Because the unittest step
  failed, the C checks that `make check` runs afterwards did not run.
- `build_host.py` rebuilt the runtime with the remembered FPS and DLC inputs;
  new FPS manifest `8bc14228c1846fa0fae35421aa48702617f6cc80b2379753bf1e06dd37a1dfcf`
  (adapter changed); DLC manifest unchanged
  (`7fdb92da38e371a851b218c6fa07d31779bb7ffb77d35c023e4c39578638c340`).
- `package_native_app.py` repackaged `build/acnh-3.0.1/Animal Crossing New Horizons.app`
  (exit 0). Source revision `1b52cf709fa18cdc81531244557bb14dcf02afa3-dirty`.
- Packaged checks (script and logs in the session scratchpad, not retained):
  version 3.0.1; `LSMinimumSystemVersion` and Mach-O `minos` 27.0 for runtime and
  launcher; FPS bundle, adapter and runtime identity; DLC bundle and runtime
  identity (3 DLCs); bundled loader `probe` passed at 30 FPS (no corrections)
  and 60 FPS (6,417 installed); `probe-dlc` passed three times (1,173 files,
  622,961,944 bytes): full hash, record reused, and forced full hash with a
  temporary proof directory; launcher `--check` and
  `codesign --verify --deep --strict` passed. The owner's 11 save files were
  unchanged by these checks.
- Not run: GUI launch, gameplay at either frame rate, DLC gameplay, 1.2.1 app
  rebuild. 3.0.1, its 60 FPS mode and its DLC support remain experimental.

## Follow-up: 120 FPS question and 60 FPS play log

> I’ve been playing for over thirty minutes now, and the frame rate has remained consistently stable at 60 fps. Would it be possible to add support for 120 fps and higher graphics settings?

> Forget it, then—just focus on further refining the 60 fps support instead.

No code was changed for these requests. The owner's play session with this build
(`last-run.log`, 216,000 frames, about 60 minutes, 60 FPS with 6,417 corrections,
docked, 120 Hz display) was analysed:

- Frame time p50 16.67 ms; on-screen cadence 16.67 ms; no dropped presents while
  the window was visible; GPU about 2 ms and main-thread work 1.4-2.7 ms per frame;
  no audio underruns.
- 47 long frames from first-use shader/pipeline compilation (3.1 s total, worst
  347 ms) and 238 other long frames (median 26.9 ms). The local pipeline record
  grew from 1,218 warmed pipelines to 1,818 entries; the next launch's warm-up count
  was not yet checked.
- Frames were dropped only during three 7-10 s periods with the window hidden.
- The pinned SpeedFix commit is still upstream `main` (v1.4.2). Its remaining
  measured pace differences (for example the first K.K. Slider concert ending
  0.65 s early) are mod data and were not changed.

This is the owner's gameplay observation at 60 FPS; DLC gameplay and other scenes
remain unverified.

## Not changed

- OLSC command 14 result `0xd401` for enabling backup (correct OLSC result
  unverified) and its placement inside the FPS commit (no history rewrite).
- The absolute `ACNH_DLC_DEFAULT_DIR` fallback (debug information already
  embeds local paths; the launcher always sets `ACNH_DLC_DIR`).
- The pre-existing untracked work logs from 2026-10-28/29 were left untouched.
  Nothing was committed or pushed.
