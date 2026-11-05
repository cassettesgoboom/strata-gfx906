# gfx906 current state

Checked 2026-11-05. Update this page when a test or source decision changes.

| Item | Exact state |
| --- | --- |
| Upstream source base | `Niko1221/Strata` v0.2.10, `ffa80d73133ea5c548aefe57889a16e8085a938f` |
| Existing fork main at checkout | `cassettesgoboom/strata-gfx906` `e063ec6cf2d9df86626b5746839f086cffbde78e` |
| Fork default branch | `integration/upstream-v0.2.10-gfx906` since 2026-11-05; historical `main` remains available and unchanged |
| New integration branch | `integration/upstream-v0.2.10-gfx906`, based on upstream `ffa80d73`; smoke/native code commit `5dddd2cd85008b0c796a94dd2108fbb1ea6102a7` includes one HIP DFlash2 guard fix. Later docs-only commits may follow. |
| Archived experimental binary | SHA256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`; current source has not reproduced it |
| Smoke/native binary | SHA256 `0a68304e239e148759f5cd6ad1b66950c53c49356d10225ad5df8ca6b2b68a84`; distinct from the archived benchmarked binary |
| Final local image candidate | `strata-gfx906:0.2.10-v0210-20261105-final`, local and unpublished; see [image candidate record](IMAGE-CANDIDATE-2026-11-05.md) |
| Historical AB/CD source | Draft PR [#4](https://github.com/cassettesgoboom/strata-gfx906/pull/4), based on v0.1.41; not merged into this branch |
| Current upstream gfx906 | Opt-in HIP source build exists; the smoke/native code commit passed one dual-MI50 short smoke using a stopped prior image candidate |
| Current upstream batch MTP | Supported opt-in path; the prior candidate's short smoke exercised MTP, while multi-agent behavior on this branch remains untested |
| AB/CD correctness | Exact native token IDs and persistent recurrent-state parity are open; keep experimental |
| Smoke result scope | Dual-MI50 gfx906 K8/V4 serial short smoke passed on an existing external Swift model using the stopped prior candidate; corrected-metadata final image has not had a GPU inference smoke |
| Archived benchmark relation | Historical rates belong to the archived binary above and do not describe this integration branch |

## Next ordered work

1. Review the one remaining narrow drafter-device cleanup candidate in
   [UPSTREAM-DELTA.md](UPSTREAM-DELTA.md) only if a current-source test justifies
   it. Keep historical AB/CD on its draft branch.
2. Before a Docker Hub release, complete the image-specific and publication
   gates in [IMAGE-CANDIDATE-2026-11-05.md](IMAGE-CANDIDATE-2026-11-05.md).
3. Repeat the short model smoke after any native or server code change. Keep
   correctness and sustained performance conclusions separate.

Do not treat the archived benchmark table as evidence for this branch. Preserve
the existing fork main, historical PR, old image and source snapshots.
