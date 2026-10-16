# Known limitations and open validation

- The source at upstream base `296b59d2f73c8f04a805df29c2fa97655adace78` has not been shown here to reproduce the
  published native artifact `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb` or OCI index
  `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
- There is no GPU validation of upstream v0.1.44.1 in the current fork evidence.
- Public hardware evidence is limited to dual MI50 32 GB and K8/V4 configuration. It does not establish behavior on
  one card, other gfx906 cards, other capacities, or other KV configurations.
- AB/CD switches are opt-in. Their correctness and performance status remains open; the switch existing or compiling
  does not establish parity.
- Token parity and state parity remain open. Do not use matching short output as a substitute for session-state
  validation.
- The inherited build instructions do not establish that current dependencies, compilers, or ROCm versions can
  reproduce an artifact. Record the exact toolchain and source when validating.
- CPU-only checks and compile-only results cannot establish GPU correctness, runtime stability, or performance.

Close an item only with an identified report that includes source and artifact identities, exact settings, workload,
observed outputs, and limitations. Keep untested cases explicit.
