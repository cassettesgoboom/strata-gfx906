# Historical MI50 comparison baseline

These are cached multi-agent measurements from the archived experimental
Docker image, on two 32 GB MI50s. They are comparison points for future
same-method tests, not performance claims for the current integration source.

| Mode | Actual context per agent | Strict common-overlap tok/s | Whole-wave tok/s |
| --- | ---: | ---: | ---: |
| P2 serial | ~96K | 38.43 | 33.35 |
| P2 serial | ~152K | 45.19 | 36.19 |
| P3 serial | ~99K | 52.46 | 41.67 |
| P3 serial | ~152K | 47.37 | 35.93 |
| P4 AB/CD opt-in | ~33K | 67.10 | 55.73 |
| P4 AB/CD opt-in | 102K | 71.17 | 53.94 |

Strict overlap is estimated from client SSE timestamps over the interval in
which every lane emitted output. Whole-wave rate uses the entire generation
wave. These rows came from different workloads and schedulers, so they do not
establish a causal AB/CD speedup. The 102K P4 output lengths were
512/512/512/473; the final lane stopped naturally. P2 ~192K demonstrated
cached continuation with only 65 output tokens per lane, so sustained decode
at that depth is unmeasured. AB/CD exact token and recurrent-state parity is
unqualified.

Public source: the existing fork's [README](https://github.com/cassettesgoboom/strata-gfx906/blob/main/README.md),
[EVIDENCE](https://github.com/cassettesgoboom/strata-gfx906/blob/main/docs/gfx906/EVIDENCE.md), and
[PROVENANCE](https://github.com/cassettesgoboom/strata-gfx906/blob/main/docs/gfx906/PROVENANCE.md).
The archived OCI index digest is
`sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
