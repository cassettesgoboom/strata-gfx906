# gfx906 upstream delta

This note records the public upstream relationship for the gfx906 work. It does not claim that the public source tree reproduces the published container.

## Public source and change status

- The public Strata source is [Niko1221/Strata](https://github.com/Niko1221/Strata). The evidence worktree's upstream base is `296b59d2f73c8f04a805df29c2fa97655adace78`.
- [PR #1102](https://github.com/Niko1221/Strata/pull/1102) is closed. Its effective equivalent is already present upstream, so it is not a unique delta for this image.
- [PR #1242](https://github.com/Niko1221/Strata/pull/1242) and [PR #1253](https://github.com/Niko1221/Strata/pull/1253) are open. Their original changes were locally ported for the experimental build.
- The AB/CD speculative path is custom local source and is unpublished. Its exact-token and state parity remain open questions. It is opt-in.
- The Oct 15 container was built from v0.1.41 experimental source. That build is not currently reproducible from the stated upstream HEAD. The published image digest is recorded in [PROVENANCE.md](PROVENANCE.md).

## Limits

These facts describe source and review status only. They do not prove that any commit or current source tree produced the published image. In particular, do not present the public source fork as a reproduction of that image. A source-to-image claim needs a build record and matching artifact evidence.

## License

The [upstream LICENSE](https://github.com/Niko1221/Strata/blob/main/LICENSE) identifies Strata as MIT licensed. Retain its copyright and permission notice in redistributions. ROCm components have separate component-level licensing; see [AMD's ROCm license table](https://rocm.docs.amd.com/en/latest/about/license.html) and the caveat in [RELEASES.md](RELEASES.md).
