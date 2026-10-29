# Work log: Publish the dedicated ACNH branch from latest main

- **Date:** 2026-10-29
- **Branch:** `acnh`, based directly on fork `origin/main` at
  `032a05dff7215177912edfb2d01c9e20089d92a7`
- **Related:** [ACNH 3.0.1 bring-up and crash correction](2026-10-29-acnh-3.0.1-bringup.md)
- **Commit:** The initial ACNH commit containing this record; owner identity
  `Sqhh99 <sqhh99@gmail.com>`
- **Publication target:** `origin/acnh` on `Sqhh99/MacNativeGames`

## 1. Request

> 新建一个分支acnh，提交commit，acnh这个分支就专门用来优化acnh（添加到AGENTS.md和CLAUDE.md），并推送到远端仓库acnh，

The owner then corrected the initial branch baseline before any commit or push:

> 等一下，你是以sqhh99为基础分支吗？不要这样，以main分支为基础分支，这样我方便给原仓库提交pr， fork的main分支仓库已经更新了，你可以拉取最新的main分支代码，再基于最新的main分支代码，创建acnh分支，提交commit

Use the latest fork main as the contribution baseline, preserve only the ACNH
changes, document the dedicated branch, commit them, and publish the branch.

## 2. Plan

1. Inspect local changes and remote branches. The original `acnh` branch had
   no new commits and had not been pushed when the owner corrected its baseline.
2. Fetch only `origin/main`, preserving the owner's unrelated work and local data.
3. Back up the scoped source patch/new files and stash the selected pending
   changes. Fast-forward local main to the fetched main snapshot and recreate
   `acnh` there. Reapply only ACNH changes and its records.
4. Add focused AGENTS/CLAUDE guidance, run source checks, stage only the requested
   files, and commit with the owner's identity.
5. Push `HEAD:refs/heads/acnh` to the owner's fork and compare its remote hash with
   the local branch. No PR is requested by this task.

## 3. Files changed

| File | Change |
|---|---|
| `games/acnh/` | Preserve the experimental 3.0.1 adaptation and post-introduction pctl correction from the linked work log |
| `AGENTS.md` | Define `acnh` as the dedicated ACNH branch, based on the latest requested fork main; scope, identity, local asset/build hygiene and verification rules |
| `CLAUDE.md` | Apply the same branch policy and game-local build/test workflow |
| `docs/work-logs/2026-10-29-acnh-3.0.1-bringup.md` | Link the implementation history to the main-based publication request |
| This record | Document the corrected branch baseline, preservation, checks and publishing scope |

The fork main does not contain AGENTS.md or CLAUDE.md, so focused files were added
without carrying the owner's unrelated Zelda guidance or `sqhh99` commit history.
The owner's earlier work-log edit remains local and is excluded from staging.
Source/backups and a preservation stash are retained locally; original game inputs,
saves, downloaded archives and build outputs are not part of the commit. Local
`.git/info/exclude` rules hide the artifact/input directories without altering the
shared `.gitignore`.

This is AI-assisted branch administration and documentation around the AI-assisted
implementation described in the linked bring-up record. The verification below
is based on executed commands.

## 4. Verification

- `git fetch origin main` completed; fetched fork tip is `032a05d`. No
  `upstream/main` fetch was performed and no personal change was committed to main.
- Before applying the ACNH changes, `HEAD`, local `main`, and `origin/main` all
  identified that exact commit. The fetched main's ACNH files were unchanged from
  the adaptation's starting source, so its patch applied without conflicts.
- ACNH tests on the main-based checkout: **23 passed**.
- Root `make check` on this new baseline: **failed**, 1,246 Python tests,
  163 skips and two errors. `test_a_cancel_kills_tar` and
  `test_a_timeout_kills_tar` in `tests/test_builder_mod_archive.py` both raise
  `FileNotFoundError` for their temporary `tar.pid`. Running just those two tests
  reproduces both errors. The test and its builder modules are unchanged from
  `origin/main`; no unrelated fix is included. The gate's later native phase was
  not reached in this run.
- `git diff --check` passed before staging. Commit scope and absence of binaries,
  game inputs, keys, fonts, saves and build output are checked against the index.
- No new app build or gameplay replay was performed for this branch-only request.
  The earlier app/probe results and known graphics/gameplay limitations remain in
  the linked implementation record; the existing app still records its earlier
  source baseline until explicitly rebuilt.
- Branch commit identity, one-commit ancestry above main and remote equality are
  verified after creating/publishing the commit and reported with its hash.

## 5. Open items

The experimental port's remaining gameplay/graphics coverage and the two existing
main-based archive-test failures are not resolved by this publication task. No PR,
merge, DMG, installation, remote-main push or unrelated source change is included.
