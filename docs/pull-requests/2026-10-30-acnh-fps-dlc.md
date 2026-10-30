# PR: feat(acnh): 3.0.1 selectable 60 FPS and the three DLCs

- **Date:** 2026-10-30
- **Branch:** `feat/acnh-3.0.1-fps-dlc` → `ly05010419/MacNativeGames` `main`. The owner asked for this upstream PR on 2026-10-30. The branch carries only the `games/acnh` changes; the fork's `AGENTS.md`, `CLAUDE.md`, work logs, reviews and PR records stay on `acnh`.
- **Base commit:** `933b6a0` (local `main` = fork `main` = `upstream/main`, which already contains #1305). `acnh` was synced with it in merge `3a22ad1`.
- **Commits** (27 files, +1,465 / −44):
  - `02c5f0a`: selectable 30/60 FPS (`323d131` without its work log);
  - `3290424`: the three pinned DLCs (`1b52cf7` without its review and work log);
  - `123739c`: review follow-up fixes (`0a67bfa` without its review and work log).
  - Commit messages point to the records on the fork's `acnh` branch. The branch's `games/acnh` is byte-identical to `acnh` at `3a22ad1`.
- **Pull request:** [ly05010419/MacNativeGames#1393](https://github.com/ly05010419/MacNativeGames/pull/1393), opened 2026-10-30. Verified: open, base `main`, head `Sqhh99:feat/acnh-3.0.1-fps-dlc`, 3 commits, 27 files (+1,465 / −44), mergeable.
- **Related records:**
  - [sync and PR work log](../work-logs/2026-10-30-acnh-sync-main-fps-dlc-pr.md);
  - [60 FPS work log](../work-logs/2026-10-29-acnh-60fps.md);
  - [DLC work log](../work-logs/2026-10-29-acnh-dlc.md);
  - [review](../code-reviews/2026-10-30-acnh-fps-dlc.md) and [follow-up work log](../work-logs/2026-10-30-acnh-fps-dlc-optimizations.md);
  - [previous PR #1305](2026-10-29-acnh-3.0.1.md).

The PR description follows.

---

## Summary
Follows #1305. For **Animal Crossing: New Horizons 3.0.1** only, this adds two optional, experimental features that players set up from their own files:

- **30 / 60 FPS selection.** 60 FPS runs at the normal game speed, using [tmouh's ACNH 60 FPS + SpeedFix](https://github.com/tmouh/acnh-60fps) supplied by the player.
- **The three DLCs.** Pocket Camp Special Order Ticket, Nook Inc. Silk Rug and Happy Home Paradise load from the player's own NSPs.

Without these inputs, a build behaves as it does today: 30 FPS and no DLC. 1.2.1 is not affected. Everything is under `games/acnh/`.

## 60 FPS
The game counts time in updates tuned for 30 per second, so unlocking 60 FPS alone runs everything twice as fast. tmouh's SpeedFix corrects this in two ways:
- 6,417 code and data words in `main`;
- the parameter file and three villager data files.

**What the player does.** Pass the mod's source checkout to `build_host.py` (`--fps-mod <dir>`, pinned to commit `e5e03e6`, v1.4.2) and repackage. **Settings > Display** then offers 30 or 60 FPS. The choice is saved in `frame-rate.txt` and applies at the next launch, because the code and parameter corrections must load together. 30 stays the default.

**How it is checked:**
- **Build time** (`tools/prepare_fps.py`):
  - checks the hashes of the six source files and of the original NSO and RomFS;
  - checks every patch site's original word against both the original and the rewritten `main`;
  - rejects any replacement word the instruction rewriter would have had to gate (`svc`, system registers, x18), or one that branches out of the code or into rewritten code.
  - The parameter overlay is derived from the player's own `StaticParam.pack` and then verified.
- **Launch** (`runtime/frame_rate.c`):
  - the loader rechecks every original word before changing any of them, then seals executable memory before the game starts;
  - nothing is patched on disk.
- **Presentation:** at 60 FPS each frame is presented on every 60 Hz tick. Selecting 30 locks the interval to 2. Builds without the data keep the game's own interval.
- **Licence:** the mod is **CC BY-NC 4.0** and none of it is in this repository. Its LICENSE and attribution are packaged with a build that uses it.

## DLC
Each DLC is pinned by its NSP SHA-256, RomFS SHA-256 and file count (`assets/expected-dlc-v0.json`). Any one or more of the three can be supplied.
- **Building:**
  - `tools/prepare_dlc.py` builds read-only images;
  - `build_host.py --dlc <dir>` compiles the matching manifest into the runtime;
  - the packager refuses a runtime built for a different DLC set.
- **Runtime** (`runtime/dlc.c`):
  - answers `nn::aoc` count/list and `nn::fs` `MountAddOnContent` / `QueryMountAddOnContentCacheSize`, which are the four AddOnContent imports 3.0.1 uses;
  - serves bounded, read-only file slices and rejects path traversal.
- **Integrity:**
  - each image's full hash is checked once;
  - after that, a verification record is reused while the file's device, inode, size and times are unchanged, the same rule the base RomFS uses;
  - `TOTK_ROMFS_VERIFY=full` forces a fresh hash;
  - a missing or changed image stops the launch instead of hiding content a save may need.

## Other changes
- **Backup setting fix:** OLSC `SetSaveDataBackupSetting` (command 14) now answers. The 3.0.1 client calls it to turn backup off when loading an existing island, and before this fix the game stopped there.
- **Build options:** `build_host.py --no-fps-mod` / `--no-dlc` forget a remembered input.
- **Packaging:** identities for the FPS and DLC bundles. The launcher sets `ACNH_FPS_ASSETS` and `ACNH_DLC_DIR`.

## Testing
- **Tests:** ACNH suite, 51 tests, passed. Root `make check` passed: 1,302 tests, 169 skipped, plus the C checks.
- **App:** rebuilt and repackaged 3.0.1 with both inputs at the merge with `main` `933b6a0`. These checks passed:
  - version 3.0.1 and deployment target 27.0 for the runtime and launcher;
  - FPS and DLC bundle identities;
  - bundled loader probe at 30 FPS (no corrections) and 60 FPS (6,417 installed);
  - DLC probe three times: first launch hashes in full, second reuses the record, third is forced. It covers all 1,173 files and 622,961,944 bytes;
  - launcher `--check`;
  - `codesign --verify --deep --strict`.
- **Play (Apple M6, 120 Hz display, docked):** one session of about 60 minutes (216,000 frames) at 60 FPS with all three DLCs mounted:
  - frame time p50 16.67 ms in every 300-frame window; the median of the windows' p95 values was 17.01 ms, and the worst window's p95 was 19.73 ms;
  - no dropped presents while the window was visible;
  - GPU about 2 ms per frame;
  - no audio underruns.
  - Remaining hitches were first-use shader compiles, which the local cache keeps for later launches.
- **Not tested:**
  - DLC-specific content (for example Happy Home Paradise work) was not played;
  - 1.2.1 was not rebuilt; its pins and code paths are unchanged.

## Known limitations
- 60 FPS has no real-time correction. A machine that can't hold 60 slows the game in step, and long first-use shader compiles briefly do the same.
- The mod's own measurements list a few actions still slightly off the 30 FPS pace. The largest is the end of K.K. Slider's first concert, 0.65 s early.
- Both features stay experimental until more of the game is played.

Prepared with AI assistance (Claude Code, Claude Opus 5.5; the first FPS and DLC drafts were written with GPT), play-tested by me.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
