# CLAUDE.md

Repository contribution and ACNH branch policy:

@AGENTS.md

## ACNH focus

- Use `acnh` for Animal Crossing: New Horizons development and optimization.
  Its contribution baseline is the latest requested fork `origin/main`, not
  `sqhh99`; keep unrelated owner history out of upstream-facing ACNH changes.
- ACNH carries its own runtime, graphics layer, instruction rewriter, tools and
  pinned translator in `games/acnh/`. Follow its README and CONTRIBUTING.md.
- The game's ARM64 code runs natively after checked ahead-of-time rewriting.
  Fix platform/ABI/service issues in the host; never add CPU emulation, copy
  emulator services, hand-edit rewritten binaries or weaken input hash checks.
- Preserve verified 1.2.1 behavior while adding explicit newer-version profiles.
  Treat 3.0.1 as experimental and record unresolved gameplay/graphics issues.

## Local workflow

Reuse `build/acnh-3.0.1/work/venv` and the existing version work folders. The
full prepare/host/package commands and required libraries are documented in
`games/acnh/README.md`. Compiling `acnh-native` alone does not update the app.

```sh
build/acnh-3.0.1/work/venv/bin/python -B -m unittest discover -s games/acnh/tests -v
make check PYTHON="$PWD/build/acnh-3.0.1/work/venv/bin/python"
```

Keep extracted data, shader caches and saves out of Git. Preserve local data and
unrelated changes when switching baselines. Validate the completed app as required
by AGENTS.md, and record what was actually built, probed and played. Creating a
commit or publishing a branch does not make an experimental port a verified release.
