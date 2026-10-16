# gfx906 current state

**Recorded:** 2026-10-16. **Stage:** public gfx906 foundation merged by PR #2, with a hosted CPU workflow; historical AB/CD source is under draft review.

- **Source base:** upstream `296b59d2f73c8f04a805df29c2fa97655adace78`.
- **Archived native binary:** SHA-256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`.
- **Archived OCI index:** `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
- **Public fork:** main retains upstream ancestry and [PR #2](https://github.com/cassettesgoboom/strata-gfx906/pull/2) is merged. The CPU tool passed 30 synthetic tests locally; this does not validate GPU execution. A clean-checkout agent completed onboarding using only public files.
- **Archived throughput evidence:** P4 AB/CD, four approximately 102K histories with cached followups: strict SSE-estimated 71.17 tok/s; whole-wave 53.94 tok/s. P3 serial, three approximately 152K histories at 512 tokens/lane: 47.37 strict and 35.93 whole-wave tok/s. P2 serial, two approximately 152K histories at 512 tokens/lane: 45.19 strict and 36.19 whole-wave tok/s. P2 at approximately 192K with cached histories and only 65 output tokens/lane is a capacity result, not a throughput result. These archived measurements apply to the pinned binary and public dual-MI50 32 GB / K8-V4 scope only.
- **Current source:** upstream v0.1.44.1 already includes gfx906, K8/V4, and serial batch-MTP paths; see [the dated upstream map](UPSTREAM-DELTA.md). No GPU validation of current fork HEAD has been done, and archived binary results do not validate it. [Draft PR #4](https://github.com/cassettesgoboom/strata-gfx906/pull/4) preserves a privacy-adapted historical AB/CD source candidate against v0.1.41 for review only. It does not change main, reproduce the archived executable, or pass exact native-token and recurrent-state parity.

See [evidence index](EVIDENCE.md) for scope and provenance. The [build-receipt schema](../../benchmarks/gfx906/build-receipt-v1.schema.json) supports future reproducible build records. **Next development action:** resolve the source-to-image build gap in [Issue #1](https://github.com/cassettesgoboom/strata-gfx906/issues/1), then separate the remaining AB/CD delta from current upstream and validate an isolated gfx906 build and exact token/state parity before considering a current-main port.
