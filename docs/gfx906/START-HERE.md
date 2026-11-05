# gfx906 integration: start here

This branch starts from upstream Strata v0.2.10. It is a new integration line
for MI50/gfx906, not a rebuild of the archived Winglab image. Read
[CURRENT-STATE.md](CURRENT-STATE.md) before editing or benchmarking and
[BASELINE.md](BASELINE.md) before comparing rates.
For a public-source gfx906 build and an unpublished local image candidate, see
[BUILD-AND-IMAGE.md](BUILD-AND-IMAGE.md).
Use [WORKFLOW.md](WORKFLOW.md) for branches, upstream sync, and pull requests.

## Git layout

- `origin` is the existing `cassettesgoboom/strata-gfx906` fork. Its `main` and
  historical branches remain available for source and evidence review.
- `upstream` is `Niko1221/Strata`. This integration branch begins at the
  upstream v0.2.10 commit recorded in CURRENT-STATE.
- Make each selected source port a focused commit on this integration line.
  Compare against upstream first; do not cherry-pick the old AB/CD draft PR.
- Do not push or publish a new image until the source diff, privacy review,
  build, and model smoke have receipts.

## A new agent's first checks

```sh
git status --short --branch
git remote -v
git remote get-url upstream >/dev/null 2>&1 || git remote add upstream https://github.com/Niko1221/Strata.git
git fetch upstream main --tags
git rev-parse HEAD origin/main upstream/main 'v0.2.10^{commit}'
rg -n 'STRATA_HIP_GFX906|CMAKE_HIP_ARCHITECTURES' CMakeLists.txt docs/AMD_HIP.md
```

These clone-only CPU checks need no GPU or model files:

```sh
python strata.py --help
python tools/test_setup_choices.py
python tools/test_setup_build_archs.py
```

Previously observed results were 59 passing checks for `test_setup_choices.py`
and 4 for `test_setup_build_archs.py`. Re-run them for the checkout being
reviewed; they exercise CLI/setup logic only and do not establish HIP
compilation, MI50 runtime behavior, correctness, or performance.

Use [docs/AMD_HIP.md](../AMD_HIP.md) for the current build interface. Record
the model identity, native binary SHA256, source commit, toolchain, flags,
hardware class, actual output, and cache evidence for each test. A completed
HTTP request alone does not establish multi-agent decode overlap or state
parity. The archived AB/CD source is in the fork's draft PR #4; its runtime
ownership and native token/state parity remain open.

Local private source material may be staged under `private/` by an authorized
operator. It is excluded from Git locally; never add it to a commit or send it
to an external agent. Public evidence and source changes must be selected and
reviewed explicitly.
