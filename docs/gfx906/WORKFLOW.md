# Public source workflow

This guide covers source changes in the public gfx906 fork. Read
[`AGENTS.md`](../../AGENTS.md), [`START-HERE.md`](START-HERE.md), and
[`CURRENT-STATE.md`](CURRENT-STATE.md) before choosing work. The integration
branch based directly on upstream Strata v0.2.10 is the reviewed development
line. Use `CURRENT-STATE.md` for its source base and latest public status.

The existing fork `origin/main` and its historical branches are reference
material. Keep `origin/main` intact and preserve the historical AB/CD draft
lineage for review. Do not move integration work onto `main`, rewrite
historical branches, or treat the old AB/CD draft as an approved patch set.

## Check a fresh clone

A fresh clone of the fork may not have an `upstream` remote. Check remotes and
add the public upstream only when it is missing:

```sh
git status --short --branch
git remote -v
git remote get-url upstream || git remote add upstream https://github.com/Niko1221/Strata.git
git fetch upstream main --tags
git fetch origin main --tags
git branch -avv
git rev-parse 'v0.2.10^{commit}' upstream/main origin/main
```

As of 2026-11-05, `integration/upstream-v0.2.10-gfx906` is published and is
the fork's default branch. A fresh clone of the repository lands on this line.
Confirm those live refs and that its upstream merge base is the recorded
v0.2.10 commit before using it. If the branch is unavailable, do not
substitute historical `origin/main`; recover the reviewed line from its
recorded public source history before creating topic work.

## Make a focused change

Start each feature or fix from the verified integration branch in a new topic
branch. Keep the change small enough to review as one problem:

```sh
git switch integration/upstream-v0.2.10-gfx906
git switch -c feature/my-focused-change
```

Before porting historical work, compare it with both the current upstream
source and the integration branch. The old AB/CD draft is based on an earlier
Strata version; do not cherry-pick it wholesale. Port only source behavior that
is still absent, needed, and covered by a focused test. Keep experimental
behavior opt-in until its correctness gate is met.

## Validate and review

Run the relevant CPU-only checks first. The clone checks listed in
[`START-HERE.md`](START-HERE.md) are:

```sh
python strata.py --help
python tools/test_setup_choices.py
python tools/test_setup_build_archs.py
```

Add the focused tests for the changed code and report failures as well as
passes. CPU checks do not qualify HIP compilation or GPU behavior. When the
change requires gfx906 validation, run the authorized build and MI50 smoke
only after the CPU checks pass. Keep compile, runtime correctness, MTP
activity, parity, and performance as separate claims; record source and binary
identities and the actual test scope.

Open a small pull request into the verified integration development line, not
the historical fork `main`. Confirm the repository's current default and target
branch before opening it. Describe the change, source base, CPU
checks, any gated MI50 evidence, and the limits of what was tested. Preserve
historical branches and do not force-push them or the integration line.

This branch/default status is a dated snapshot. Verify it from the public
repository when continuing work later.
