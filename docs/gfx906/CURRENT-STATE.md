# gfx906 current state

Checked 2026-11-05. Update this page when a test or source decision changes.

| Item | Exact state |
| --- | --- |
| Upstream source base | `Niko1221/Strata` v0.2.10, `ffa80d73133ea5c548aefe57889a16e8085a938f` |
| Existing fork main at checkout | `cassettesgoboom/strata-gfx906` `e063ec6cf2d9df86626b5746839f086cffbde78e` |
| New integration branch | `integration/upstream-v0.2.10-gfx906`, HEAD `5dddd2cd`, based on upstream `ffa80d73`; includes one HIP DFlash2 guard fix |
| Archived experimental binary | SHA256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`; current source has not reproduced it |
| Integration-branch smoke binary | SHA256 `0a68304e239e148759f5cd6ad1b66950c53c49356d10225ad5df8ca6b2b68a84`; distinct from the archived benchmarked binary |
| Historical AB/CD source | Draft PR [#4](https://github.com/cassettesgoboom/strata-gfx906/pull/4), based on v0.1.41; not merged into this branch |
| Current upstream gfx906 | Opt-in HIP source build exists; this integration branch passed one dual-MI50 short smoke |
| Current upstream batch MTP | Supported opt-in path; short smoke exercised MTP, while multi-agent behavior on this branch remains untested |
| AB/CD correctness | Exact native token IDs and persistent recurrent-state parity are open; keep experimental |
| Integration-branch smoke | Dual-MI50 gfx906 K8/V4 serial short smoke passed on an existing external Swift model; this is a smoke result only, with no performance or correctness qualification |
| Archived benchmark relation | Historical rates belong to the archived binary above and do not describe this integration branch |

## Next ordered work

1. Compare historical fork changes with this integration base. Port only
   behavior absent upstream and justified by a focused test.
2. Repeat the short model smoke for any changed binary. Keep correctness and
   sustained performance conclusions separate.

Do not treat the archived benchmark table as evidence for this branch. Preserve
the existing fork main, historical PR, old image and source snapshots.
