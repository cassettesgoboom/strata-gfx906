# gfx906 local image candidate — 2026-11-05

This is a record of the final corrected-metadata image built locally from the
gfx906 integration work. It is unpublished and has not been pulled remotely.

| Field | Value |
| --- | --- |
| Local tag | `strata-gfx906:0.2.10-v0210-20261105-final` |
| Image ID | `sha256:4ac90e7a7bb41006f98a79125245dc9658e1b7136b4f346f11b59e49cff48125` |
| Size | 1,651,061,064 bytes |
| Platform | `linux/amd64` |
| ROCm gfx906 base index digest | `sha256:622c025824d465faa0f5e59eea4f723845032011df273c3b11e25031965fc428` |
| Smoke/native source code commit | `5dddd2cd85008b0c796a94dd2108fbb1ea6102a7` |
| Native binary SHA256 | `0a68304e239e148759f5cd6ad1b66950c53c49356d10225ad5df8ca6b2b68a84` |
| Engine component version | `v0.1.56` |
| Engine package manifest SHA256 | `8589be0b30cd7a4befdbbe01d1cad95e015438622b82018038fb4405efd0cd96` |

Package verification, binary dependency checks, and final-image `components
engine` GPU discovery (`usable=true`) passed. No model weights are bundled.

## Validation boundary

The actual dual-MI50 K8/V4 short inference smoke was run on a prior candidate
image. That candidate used the same native engine binary and Terminal source,
but its engine component version metadata was incorrectly set to `0.2.10`; it
is stopped. Its two requests returned HTTP 200 and produced 75 prompt / 146
output tokens, then 173 prompt / 130 output tokens with 70 native prompt tokens
reused. MTP accepted/offered counts were 97/120 and 76/88.

The corrected-metadata final image recorded above has not had a GPU inference
smoke and has not been pulled remotely. The prior candidate's smoke does not
validate this final image as a release. This image is not published and must
not be described as a published or validated release. No performance or
correctness qualification is established by these checks.

The local image still carries upstream's generic OCI source label. Before a
public tag, record the exact fork revision in the image metadata, review the
redistribution notices for bundled ROCm libraries, run an image-specific GPU
smoke, and verify an external pull by immutable digest. Preserve the existing
published tags and `latest`.
