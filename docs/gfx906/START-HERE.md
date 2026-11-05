# gfx906 integration: start here

This branch starts from upstream Strata v0.2.10. It is a new integration line
for MI50/gfx906, not a rebuild of the archived Winglab image. Read
[CURRENT-STATE.md](CURRENT-STATE.md) before editing or benchmarking and
[BASELINE.md](BASELINE.md) before comparing rates.

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
git rev-parse HEAD origin/main upstream/main 'v0.2.10^{commit}'
rg -n 'STRATA_HIP_GFX906|CMAKE_HIP_ARCHITECTURES' CMakeLists.txt docs/AMD_HIP.md
```

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
