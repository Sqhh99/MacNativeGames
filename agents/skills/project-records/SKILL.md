---
name: project-records
description: Write the mandatory MacNativeGames documentation records — a work log after any request that changes files, a code-review archive after reviewing code, and a PR record before opening a pull request. Use whenever finishing such a request, review, or PR.
---

# Project records

This repository keeps three kinds of permanent records under `docs/`. They are
mandatory, not optional extras: a decision that exists only in a conversation is lost
the moment the session ends.

## The three records

| Record | Trigger | Directory | Language |
|--------|---------|-----------|----------|
| Work log | Any request that changes files | `docs/work-logs/` | English |
| Code review | Any code review | `docs/code-reviews/` | English |
| PR record | Before opening a pull request | `docs/pull-requests/` | English |

All three are written in English. Quote the user's request in whatever language they
wrote it.

All three use the filename `YYYY-MM-DD-<topic>.md`, where `<topic>` is a short
kebab-case slug — for a PR record, the branch topic. Use the real current date, and
write dates absolutely (`2026-08-28`, never "today" or "last week").

Cross-link the records for one piece of work: the work log links to the review and the
PR record, the review's status summary links to the work log, and the PR record links to
both. Use repo-relative links (`../work-logs/...`) so they resolve on GitHub.

## Rules that apply to all three

- **Never tick a verification box for a command you did not run.** Leave it unchecked and
  say why in the surrounding prose. This is the rule most likely to be quietly broken;
  breaking it makes every other record untrustworthy.
- **State the verification status explicitly**, including "not built, not tested". The
  checks are `make check` (what CI runs, see `.github/workflows/tests.yml`), the probes and
  tests of the part changed, and a build of every game version touched with `build_app.py`
  (macOS 26 or later on Apple silicon; iOS builds need Xcode and the iOS SDK). When one
  could not be run, that is a fact for the record, not an excuse to omit. Say per platform
  how a change was tested (built only, played on a Mac, played on an iPhone or iPad), as
  `CONTRIBUTING.md` asks.
- Disclose AI assistance honestly: which parts were AI-generated, and whether they were
  verified.
- Record what was **not** done or **not** covered as carefully as what was. Scope
  boundaries are the part a future reader cannot reconstruct.
- Quote the user's request verbatim rather than paraphrasing it.
- Never put game content, keys, saves or the paths of the owner's local game files beyond
  the repository's own `build/` and `game-assets/` layout into a record.

## 1. Work log — `docs/work-logs/YYYY-MM-DD-<topic>.md`

Written after any request that changes files, capturing the whole request → plan →
change cycle. One file per request; append a new section to the day's file when a
request is a direct follow-up to one already logged there.

```markdown
# Work log: <one-line topic>

- **Date:** YYYY-MM-DD
- **Branch:** `<branch>` (from `sqhh99` at `<commit>`)
- **Related:** links to the review archive / PR record, if any

## 1. Request
> The request, quoted verbatim
What the request actually asked for, in a sentence or two.

## 2. Plan
The plan steps, in the order they were carried out.

## 3. Files changed
| File | Change |  ← for code changes, add a third column "Addresses"
Say why each file changed, not only what changed.

## 4. Verification
What was run, what was not, and why. If something was not run, say so plainly.

## 5. Open items
What is unfinished, not covered, or needs follow-up.
```

## 2. Code review — `docs/code-reviews/YYYY-MM-DD-<short-title>.md`

Written after reviewing code, whether or not anything is fixed as a result.

```markdown
# <Title> Code Review

- **Date:** YYYY-MM-DD
- **Reviewed at commit:** `<sha>` (branch)
- **Scope:** what was read, and how (source reading, call-path tracing, running it)
- **Not covered:** the parts deliberately left out

## Status summary
One paragraph on whether the findings are implemented, plus the findings table.

| # | Finding | Severity | Implemented |
|---|---------|----------|-------------|
| 1 | ... | Medium | ❌ No — open  /  ✅ Yes — YYYY-MM-DD |

## <n>. <Finding title>
**Location:** `file:line` · **Severity:** ... · **Implemented:** ...
What is wrong, the concrete path that reaches it, and how reachable it actually is —
state reachability honestly instead of inflating severity.
**Fix.** Added when the finding is implemented; describes the change, not the intent.

## Verified correct — do not "fix" these
Things that looked like defects but are handled properly, so nobody undoes them later.
```

The `Implemented` column is the point of the document: keep it current. When findings are
later fixed, update this file in place — do not start a second review document for the
same review. Line numbers stay as they were at review time; the header records the commit.

## 3. PR record — `docs/pull-requests/YYYY-MM-DD-<branch-topic>.md`

Written **before** opening the pull request, then used as the PR body. Personal pull
requests target `sqhh99` on `Sqhh99/MacNativeGames`, never `main` (`AGENTS.md`). The
sections follow the pull request rules of `CONTRIBUTING.md`; if those change, change this
skeleton to match:

```markdown
# PR: <title>

- **Date:** / **Branch:** `<branch>` → `sqhh99` / **Base commit:** `<sha>` / **Related records:**

## Related
The Issue or Discussion ("Related to #123"), or the problem being solved. Never
"Fixes #123" / "Closes #123": the maintainer closes issues by hand.

## What changed
What players or developers will notice. Do not just paste a file list. One topic per
pull request.

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance or refactoring (no behavior change intended)
- [ ] Docs, CI, or build only

## How it was tested
- [ ] `make check` passes (or `python -m unittest discover -s tests` and the native tests CI runs)
- [ ] The probes and tests of the part changed pass (`probe-*` targets in `games/totk/Makefile`, `tests/`)
- [ ] Built every game version touched with `build_app.py` (say which; shared runtime code also with `--platform ios`)
- [ ] Played on a Mac / an iPhone or iPad (say which game version, and where in the game)
Leave a box unticked if it was not run, and say why and who needs to run it, in which
environment, before merge.

## Checklist
- [ ] I have read CONTRIBUTING.md
- [ ] No game content, keys or saves; no GPL code or code from other mods
- [ ] Existing keys, defaults and verified version tables (`expected-*.json`, `game_version.h`) unchanged, or the change is the point of the PR and called out above
- [ ] Diagnostics are off by default
- [ ] New host text has English, Chinese and Japanese (`TOTK_UI3`, or `totk_ui_ja` in `totk_ui_lang.h`)
- [ ] AI disclosure: No / Yes (say which parts, and whether you verified them)
```

The PR body and this file should say the same thing. The PR body ends with the Claude Code
generation line; the file does not need it.

## Extending this skill

A new record type needs three things: a trigger, a directory under `docs/`, and a
template here. Add a row to the table above and a numbered section, then add the trigger
to the `Mandatory records` section of `CLAUDE.md` and to `AGENTS.md` so it is reachable
without loading this file. Keep the naming convention (`YYYY-MM-DD-<topic>.md`) — it is
what makes the directories sortable and greppable by date.
