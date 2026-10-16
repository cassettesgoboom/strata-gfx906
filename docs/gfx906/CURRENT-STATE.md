# gfx906 current state

**Recorded:** 2026-10-16. **Stage:** public foundation PR #2 under hosted CPU CI review.

- **Source base:** upstream `296b59d2f73c8f04a805df29c2fa97655adace78`.
- **Archived native binary:** SHA-256 `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb`.
- **Archived OCI index:** `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
- **Integration checkout:** branch `foundation/gfx906-public` retains upstream ancestry. The revised CPU tool passed 30 synthetic tests locally; this does not validate GPU execution. A clean-checkout agent completed onboarding using only public files. Fork `main` remains at the upstream base until the reviewed foundation is merged.
- **Archived throughput evidence:** P4 AB/CD, four approximately 102K histories with cached followups: strict SSE-estimated 71.17 tok/s; whole-wave 53.94 tok/s. P3 serial, three approximately 152K histories at 512 tokens/lane: 47.37 strict and 35.93 whole-wave tok/s. P2 serial, two approximately 152K histories at 512 tokens/lane: 45.19 strict and 36.19 whole-wave tok/s. P2 at approximately 192K with cached histories and only 65 output tokens/lane is a capacity result, not a throughput result. These archived measurements apply to the pinned binary and public dual-MI50 32 GB / K8-V4 scope only.
- **Current source:** no GPU validation on upstream v0.1.44.1; the archived binary results do not validate current HEAD. The archived AB/CD delta has not been reviewed and ported into this fork. Exact native-token and recurrent-state parity remain open.

See [evidence index](EVIDENCE.md) for scope and provenance. **Next safe action:** inspect the hosted CPU check and PR review, then merge the foundation if both pass.
