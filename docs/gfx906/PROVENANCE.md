# gfx906 provenance

## Published image

| Field | Value |
| --- | --- |
| Docker Hub repository | [`cassettesgoboom/strata-gfx906`](https://hub.docker.com/r/cassettesgoboom/strata-gfx906) |
| Tag | `0.1.41-winglab-20261015-exp` |
| OCI image-index digest | `sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29` |
| Linux amd64 image digest | `sha256:a4acc3768b3917abc8e4622e112ecba82ad6b89361705e51299e304f34fd4a18` |
| Public tag last-pushed time | 2026-10-15T19:43:42.817563Z |
| Native SHA supplied for this evidence record | `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb` |

The [Docker Hub tag API](https://hub.docker.com/v2/namespaces/cassettesgoboom/repositories/strata-gfx906/tags/0.1.41-winglab-20261015-exp) returned the tag, manifest-index digest, platform image digest, and push timestamp. The tag name is a mutable reference; use the digest when identifying the published artifact. The `unknown/unknown` OCI image attached to the index is an attestation object, not another runnable platform image.

## Source relationship

The archived image is recorded as v0.1.41 experimental source, with upstream commit
`296b59d2f73c8f04a805df29c2fa97655adace78` as its source baseline. That is an archived baseline, not current
upstream HEAD. The supplied native SHA is recorded as a separate native artifact identifier; public tag metadata
does not establish that it is an image-layer checksum or that it corresponds to the container. As of the public
state check on 2026-10-17, the available records do not establish a coherent source tree that reproduces the
archived binary or a reproduction from the fork source snapshot reviewed at `af45b70bf5cb7e61a0e0825c632397190a97e18b` or current
upstream main `477ac13cbe8e582c20484871ce459d20d82df09d`. Do not claim that the current public source fork
reproduces the image.

The fork source snapshot reviewed after PR [#40](https://github.com/cassettesgoboom/strata-gfx906/pull/40) is [`3f076fea5a98f69d2fec1d364b21380eb1a67e95`](https://github.com/cassettesgoboom/strata-gfx906/commit/3f076fea5a98f69d2fec1d364b21380eb1a67e95). Later PR [#42](https://github.com/cassettesgoboom/strata-gfx906/pull/42) refreshed documentation, and PR [#43](https://github.com/cassettesgoboom/strata-gfx906/pull/43) registered existing native trace helper tests with CMake/CTest; neither changes the inference runtime. Earlier PR [#11](https://github.com/cassettesgoboom/strata-gfx906/pull/11) adds archived MI50 measurements to the README, and PR [#12](https://github.com/cassettesgoboom/strata-gfx906/pull/12) adds CPU-only synthetic trace comparison tooling. These records do not change the engine, container, tag, or image digest above. The comparator's successful comparison is not runtime parity evidence and does not update the archived image's provenance.

## Current-source compile-only artifact

PR [#52](https://github.com/cassettesgoboom/strata-gfx906/pull/52) selectively ports upstream [commit `1d6fd9f97ab09da231b35cbbd84a2879adb6d77f`](https://github.com/Niko1221/Strata/commit/1d6fd9f97ab09da231b35cbbd84a2879adb6d77f). Its [build receipt](../../benchmarks/gfx906/receipts/2026-10-18-pr1752-gfx906-hip-build.json) records a compile-only gfx906 HIP artifact with SHA-256 `805ffbf38e0e0030f99f7b62b96aa129350d96fe016d08e580abab3fe98806f8`, built from fork base `294fe5248273ec1a9c7331d81d0708ce8e66423c` plus the receipt's exact patch bundle. This artifact is not the published image, does not contain model assets, and is not the archived native executable listed above. No MI50 inference/performance validation or AB/CD token/state parity is established by this build.

An archived network-isolated pullback of the OCI index digest above recorded these in-container executable hashes:

| Artifact | SHA-256 |
| --- | --- |
| `/usr/local/bin/strata` | `ae93901c79771ace15db52942523c25fc46dd6f0d6a3b43698b28e6071c472cb` |
| Bridge | `bfda9a822dc51df433d6f240c6f2140cfdeb816575b73f8c471e409271be2fd3` |
| CPU vision | `8142525656d0cf194f68c929c3ccd2c45320bc73fde22a21363448f61d875058` |

The same archived receipt reported ROCm runtime `7.14.0-gfx906+20260802001858` and HIP configuration `7.14.60850-0000000`. These are archived pullback observations, not a fresh live inspection. They identify executable contents in that pulled artifact but do not make the source build reproducible from the current fork.

## Quiet-build source limitations

The archived quiet-build record associates the preserved executable with the published pullback engine SHA above and records a Release, gfx906 build using ROCm clang++. The source snapshot has no `.git` metadata. No publicly reviewable coherent source and patch set establishes its exact commit, full build inputs, or a reproducible build of the published executable. Private source and patch artifacts are not included or fingerprinted here; their existence does not establish source-to-binary provenance.

The source delta and review status are in [UPSTREAM-DELTA.md](UPSTREAM-DELTA.md). No private host, network, storage, container, or telemetry paths are part of this record.

## Public evidence URLs

- [Docker Hub repository](https://hub.docker.com/r/cassettesgoboom/strata-gfx906)
- [Docker Hub tag API](https://hub.docker.com/v2/namespaces/cassettesgoboom/repositories/strata-gfx906/tags/0.1.41-winglab-20261015-exp)
- [Upstream source base](https://github.com/Niko1221/Strata/commit/296b59d2f73c8f04a805df29c2fa97655adace78)
- [Strata MIT license](https://github.com/Niko1221/Strata/blob/main/LICENSE)
