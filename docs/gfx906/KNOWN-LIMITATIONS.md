# Known limitations and open validation

- The source at upstream base `296b59d2f73c8f04a805df29c2fa97655adace78` has not been shown here to reproduce the
  published native artifact `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb` or OCI index
  `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
- A current-main-equivalent binary passed a short serial dual-MI50 GPU smoke with positive cache reuse and MTP
  counters. This does not validate sustained batching, AB/CD, other hardware, or exact token/state parity.
- Public hardware evidence is limited to dual MI50 32 GB and K8/V4 configuration. It does not establish behavior on
  one card, other gfx906 cards, other capacities, or other KV configurations.
- The archived binary's AB/CD switch is opt-in. A historical source candidate is under draft review, but it has
  not been ported into current main. Archived performance does not establish correctness or token/state parity.
- Token parity and state parity remain open. Do not use matching short output as a substitute for session-state
  validation.
- The inherited build instructions do not establish that current dependencies, compilers, or ROCm versions can
  reproduce an artifact. Record the exact toolchain and source when validating.
- CPU-only checks and compile-only results cannot establish GPU correctness, runtime stability, or performance.

Close an item only with an identified report that includes source and artifact identities, exact settings, workload,
observed outputs, and limitations. Keep untested cases explicit.
