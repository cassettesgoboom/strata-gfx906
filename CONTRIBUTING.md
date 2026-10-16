# Contributing to the gfx906 fork

This fork carries experimental AMD gfx906 (wave64) work alongside upstream Strata. For supported build details and
the current evidence boundary, begin with [docs/gfx906/START-HERE.md](docs/gfx906/START-HERE.md).

Before proposing a change:

- Search existing upstream and fork issues and pull requests, then keep each change focused.
- State the base revision, source commits or patch IDs, and whether the result was built from source. A binary or
  native engine hash alone does not identify a reproducible source build.
- Keep behavior-changing switches opt-in until correctness and compatibility evidence supports a default change.
- Report build, correctness, token/state parity, and performance as separate results. Identify hardware, software,
  model/configuration, workload, and untested cases; use the upstream
  [community benchmark guide](https://github.com/Niko1221/Strata/blob/main/docs/COMMUNITY_BENCHMARKS.md) for report
  structure.
- Do not include private host paths, topology, logs, credentials, or model data in public issues or commits.

For a report or request, choose the matching checked-in form under [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/).
Include only public, reproducible details and label unavailable measurements explicitly.

Public historical evidence is not current validation of this fork. See [CURRENT-STATE.md](docs/gfx906/CURRENT-STATE.md)
and [KNOWN-LIMITATIONS.md](docs/gfx906/KNOWN-LIMITATIONS.md) before making support claims.
