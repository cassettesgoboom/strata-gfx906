# gfx906 current state

Checked 2026-11-05. Update this page when a test or source decision changes.

| Item | Exact state |
| --- | --- |
| Upstream source base | `Niko1221/Strata` v0.2.10, `ffa80d73133ea5c548aefe57889a16e8085a938f` |
| Existing fork main at checkout | `cassettesgoboom/strata-gfx906` `e063ec6cf2d9df86626b5746839f086cffbde78e` |
| New integration branch | `integration/upstream-v0.2.10-gfx906`, initially identical to upstream base |
| Archived experimental binary | SHA256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`; current source has not reproduced it |
| Historical AB/CD source | Draft PR [#4](https://github.com/cassettesgoboom/strata-gfx906/pull/4), based on v0.1.41; not merged into this branch |
| Current upstream gfx906 | Opt-in HIP source build exists; MI50 validation of this exact source is pending |
| Current upstream batch MTP | Supported opt-in path; verify actual flags and counters on the model before claiming activity |
| AB/CD correctness | Exact native token IDs and persistent recurrent-state parity are open; keep experimental |
| Current-source test | No MI50 smoke or performance result yet for this integration branch |

## Next ordered work

1. Review the upstream build and runtime flags against the existing model pack.
2. Build the unmodified upstream base for gfx906 and perform one isolated short
   inference plus cached continuation on the existing model. Record a receipt.
3. Compare the historical Winglab source and fork changes with this base.
   Port only behavior that is absent upstream and justified by a focused test.
4. Repeat the short model smoke for any changed binary. Keep correctness and
   sustained performance conclusions separate.

Do not treat the archived benchmark table as evidence for this branch. Preserve
the existing fork main, historical PR, old image and source snapshots.
