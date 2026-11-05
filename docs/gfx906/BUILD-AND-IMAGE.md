# gfx906 build and local image candidate

This is a public-source recipe for building a gfx906 native engine from the
checkout and placing that binary in a local Docker image. It is not a claim
that these commands were run for the current checkout, that another build will
reproduce the same binary, or that the resulting image has passed a GPU smoke.
The image contains software only; model weights stay outside it.

## Record the source identity

Use the exact source tree intended for the build. Record its full commit,
upstream v0.2.10 base, and working-tree state before compiling:

```sh
git rev-parse HEAD
git rev-parse 'v0.2.10^{commit}'
git status --short
```

Use a clean tree where possible. If source changes are present, preserve and
identify the complete source delta alongside the build record. A `--build-id`
string is descriptive metadata; it does not prove source-to-binary
reproducibility.

## Build the gfx906 binary

Follow the gfx906 section of [AMD_HIP.md](../AMD_HIP.md#gfx906-instinct-mi50--mi60-radeon-vii-wave64-built-from-source).
It documents a separate HIP build using the HIP 7.14 toolchain and
gfx906-enabled ROCm libraries from the community image
[`mixa3607/rocm-gfx906:7.14-complete`](https://hub.docker.com/r/mixa3607/rocm-gfx906).
Resolve and record that image's immutable digest, then use the digest-pinned
image for the build environment. The checked-out tree must include the
llama.cpp revision pinned by this Strata source.

Inside that environment, with the Strata checkout at `/src`:

```sh
apt-get update
apt-get install -y cmake ninja-build git python3 build-essential
cmake -S /src -B /src/build-906 -G Ninja \
  -DSTRATA_HIP_GFX906=ON \
  -DCMAKE_HIP_ARCHITECTURES=gfx906 \
  -DSTRATA_GGML_DIR=/src/third_party/llama.cpp \
  -DCMAKE_C_COMPILER=/opt/rocm/llvm/bin/clang \
  -DCMAKE_CXX_COMPILER=/opt/rocm/llvm/bin/clang++
ninja -C /src/build-906 strata
```

The resulting native executable is `/src/build-906/strata`. Record its
SHA-256, the full source commit, the ROCm image digest, compiler and ROCm
versions, CMake command, and build result together. These identify the
artifact and its declared inputs; they do not establish a reproducible build.
Upstream notes that some boards may need `HSA_OVERRIDE_GFX_VERSION=9.0.6` at
runtime. Setup does not build gfx906 automatically.

## Package and verify the native engine

Create a small staging directory containing the exact `strata` executable,
its required shared libraries, and any ROCm kernel/runtime data the binary
needs. Keep the stage limited to runtime files; do not place model files in
it. Preserve the binary hash in the receipt before packaging.

From the same v0.2.10 source checkout, create a HIP engine component package.
Use the engine version reported by this checkout (`0.1.56` for Strata v0.2.10)
and a build ID that records the full source revision and toolchain:

```sh
SOURCE_COMMIT="$(git rev-parse HEAD)"
ENGINE_STAGE=/path/to/engine-stage
PACKAGE_ROOT=/path/to/components/engine

sha256sum "$ENGINE_STAGE/strata"
python packaging/package_engine.py \
  --src "$ENGINE_STAGE" \
  --backend hip \
  --version 0.1.56 \
  --platform linux-x86_64 \
  --out "$PACKAGE_ROOT" \
  --entrypoint strata \
  --arch gfx906 \
  --variant gfx906 \
  --build-id "source-${SOURCE_COMMIT}-rocm-7.14-gfx906" \
  --tree
```

Set `ENGINE_PACKAGE` to the package directory printed by the command, then
verify its manifest hashes and shared-library closure:

```sh
ENGINE_PACKAGE=/path/to/components/engine/<printed-package-directory>
python packaging/package_engine.py --verify "$ENGINE_PACKAGE"
```

The component manifest identifies packaged file hashes and metadata. Keep the
native executable SHA-256, component package manifest SHA-256, complete source
revision, dirty-tree status, and toolchain/base image digest in the same build
receipt. Package verification checks the package contents and dependencies; it
does not run the engine on a GPU.

## Build an unpublished local Docker image

The upstream Docker image uses its bundled Terminal (`strata.py`,
`strata_cli`, `strata_control`, and `serve`), standalone CPython 3.12, and
hash-locked Python packages including NumPy, Jinja2, regex, PyYAML, tqdm,
requests, Pillow, and psutil. It also includes the health check and
signal-aware entrypoint. [`docker/build.sh`](../../docker/build.sh) stages
those checked-out files plus the engine package, and
[`docker/Dockerfile`](../../docker/Dockerfile) verifies package contents and
library resolution. The build fetches the runtime's pinned dependencies, but
it does not include model weights or publish the image.

Replace the base placeholder with the digest resolved from the public ROCm
image. Keep the exact checkout used for the native binary as `--repo`:

```sh
ROCM_BASE='mixa3607/rocm-gfx906@sha256:<resolved-64-hex-digest>'
SOURCE_SHORT="$(git rev-parse --short=12 HEAD)"

docker/build.sh \
  --repo . \
  --flavor hip \
  --base "$ROCM_BASE" \
  --engine "$ENGINE_PACKAGE" \
  --version "0.2.10-gfx906-${SOURCE_SHORT}" \
  --tag "strata:0.2.10-gfx906-${SOURCE_SHORT}"
```

Keep the image local. Record the selected base digest, source commit, native
binary hash, package manifest hash, image tag, and local image ID. Until a
dual-MI50 GPU smoke passes and an authorized image is pulled back by its OCI
digest and checked, this is only a local candidate, not a validated release.
Do not infer runtime correctness or performance from a successful image build.

## Keep model files external

For a later runtime smoke, mount the folder holding one model's GGUF shards
read-only at `/models`, set `MODEL_PATH=/models` plus the explicit `FAMILY` and
`MODEL`, and keep `/data` on a persistent writable volume for prepared packs,
MTP data, settings, and logs. The model folder should contain the shards
directly. Do not copy model weights into the Docker build context, image, or
source repository. Supply any API key through the runtime's supported secret
input; never write it into this document or the image.

The runtime command and GPU-device options are documented in upstream
[`docs/DOCKER.md`](https://github.com/Niko1221/Strata/blob/v0.2.10/docs/DOCKER.md)
and [`docker/entrypoint.sh`](https://github.com/Niko1221/Strata/blob/v0.2.10/docker/entrypoint.sh).
Follow those instructions for `/dev/kfd`, `/dev/dri`, device groups, IPC,
memlock, and graceful stop. The upstream gfx906 notes say vision and Qwen3.6
are not supported by this build; check `strata --families` before choosing a
model.
