# gfx906 public releases

Docker Hub tag metadata was queried on 2026-10-16 UTC from the [official public tag-list API](https://hub.docker.com/v2/namespaces/cassettesgoboom/repositories/strata-gfx906/tags?page_size=100). These are registry-reported manifest-index and Linux amd64 image digests, not checksums inferred from tag names.

| Tag | OCI index digest | Linux amd64 image digest | Last pushed (UTC) |
| --- | --- | --- | --- |
| `0.1.41-winglab-20261015-exp` | `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29` | `sha256:a4acc3768b3917abc8e4622e112ecba82ad6b89361705e51299e304f34fd4a18` | 2026-10-15T19:43:42.817563Z |
| `0.1.41-batchmtp-exp-20261008-full` | `sha256:1583250c02e0a8bd3465c75dc2246951232b9b0ea3714ab09ff8987b73d14661` | `sha256:0ad3c640bebf2c935c7d703fe49a4dc7c83d464cb5ffd8cbed7aa39805107dc9` | 2026-10-08T22:38:58.988222Z |
| `0.1.40.1-pr1102-20261007-full` | `sha256:5e65e8e3d97e6352bbae1779d0102db0eba6e633a33eb3199042d047d5e7a3dc` | `sha256:d9900b6992e1ed5a1716943c1c0721d9610294a3519c02b29361f6f1efb03e7b` | 2026-10-07T20:09:10.312401Z |
| `0.1.40.1-pr1102-20261007` | `sha256:cff67a01ce2365a93a3b43a6e46694da3a28cfb7daf229fae5180ab92dc2295a` | `sha256:d6c6aa193304d3dbfab1c54f691d9494a8523cf94dc389307874653aa8f91b34` | 2026-10-07T16:03:33.834014Z |

The API reported four active tags and an additional small `unknown/unknown` image for each OCI index. Pin and cite the index digest for the multi-platform artifact or the amd64 digest for that specific platform. Metadata does not prove image contents, build inputs, or correspondence to a source commit. The Oct 15 image's stated source and native artifact SHA are recorded in [PROVENANCE.md](PROVENANCE.md); the source tree is not currently a reproducible build of that image.

## Archived release receipt for Oct 15 image

An archived network-isolated pullback of the Oct 15 OCI index digest recorded the in-container executable hashes and ROCm/HIP versions listed in [PROVENANCE.md](PROVENANCE.md). An archived release smoke also completed a seed request with 64 output tokens, followed by a cached continuation with 47 output tokens and 672 native reused tokens. This is historical receipt evidence, not a fresh live smoke or a reproducible build from the current source fork.

## Licensing notes

The [Niko1221/Strata LICENSE](https://github.com/Niko1221/Strata/blob/main/LICENSE) is MIT. Preserve its copyright and permission notices in redistributed copies or substantial portions.

ROCm does not have one blanket license. [AMD's component licensing page](https://rocm.docs.amd.com/en/latest/about/license.html) lists different licenses by component and notes third-party licenses; some entries are custom or proprietary. Review the licenses shipped with the exact ROCm/runtime packages in any derivative image and include applicable notices and terms. Public Docker metadata alone does not identify those contents or establish license compliance.
