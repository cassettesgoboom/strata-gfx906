# Reviewing upstream changes

This repository remains a fork of [Niko1221/Strata](https://github.com/Niko1221/Strata). Preserve its Git history,
MIT notices and attribution. Record the current fork and upstream SHAs in a review before merging anything.

For a read-only comparison from a clone:

```bash
git remote -v
git fetch upstream --tags
git log --left-right --cherry-pick --oneline origin/main...upstream/main
git diff --stat origin/main...upstream/main
```

If `upstream` is absent, add `https://github.com/Niko1221/Strata.git` as that remote. Review each gfx906-related
change against [UPSTREAM-DELTA.md](UPSTREAM-DELTA.md): an upstream equivalent should not be ported again. Work on
an isolated branch/worktree and submit a focused PR. State the exact upstream base, changed source paths, build
flags, CPU tests, hardware tests if actually run, and any behavior that remains unverified. Merge reviewed upstream
commits through a normal PR; do not rewrite established public release refs or treat a successful merge as GPU
qualification. Recheck privacy and component licences before publishing derived source or binaries.

The archived AB/CD binary has a known hash, but its local source tree is a non-Git snapshot. Recover original
coherent commits and review the source delta before attempting a port. Source integration, exact token/state parity,
and throughput qualification are separate gates.
