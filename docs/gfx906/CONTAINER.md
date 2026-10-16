# Archived gfx906 container

The experimental image is available at
`docker.io/cassettesgoboom/strata-gfx906@sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
The [release record](PROVENANCE.md) identifies the native binary inside an archived digest pullback. This source
checkout has not been shown to rebuild that binary. The image contains no model weights; mount a compatible GGUF,
tokenizer/pack, and model-specific data externally. Hardware memory needs depend on the model and host.

## Pull

```bash
docker pull docker.io/cassettesgoboom/strata-gfx906@sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29
```

## Run with your own model configuration

Prepare `config.json` for the image's Strata server entrypoint. It must use container paths such as
`/usr/local/bin/strata`, `/models`, `/data`, `/cache`, and port `8080`; choose its native model arguments from the
model's own pack and the upstream Strata configuration documentation. Select two render devices on your machine
and set the paths below. The numeric render-device suffixes, GPU ordering, model memory budget, and host port are
installation-specific.

```bash
export GPU0_RENDER=/dev/dri/renderDXXX
export GPU1_RENDER=/dev/dri/renderDYYY
export MODEL_DIR=/path/to/gguf-files
export DATA_DIR=/path/to/model-pack-and-tokenizer
export CONFIG_DIR=/path/to/config-directory
export CACHE_DIR=/path/to/writable-cache
export RESULTS_DIR=/path/to/writable-results
export MEMORY_LIMIT=20g  # choose for your model and host; this is an example, not a tested minimum

docker run --rm --name strata-gfx906-exp \
  --memory="$MEMORY_LIMIT" --memory-swap="$MEMORY_LIMIT" \
  --device=/dev/kfd --device="$GPU0_RENDER" --device="$GPU1_RENDER" \
  -p 127.0.0.1:8080:8080 \
  --mount "type=bind,src=$MODEL_DIR,dst=/models,readonly" \
  --mount "type=bind,src=$DATA_DIR,dst=/data,readonly" \
  --mount "type=bind,src=$CONFIG_DIR,dst=/config,readonly" \
  --mount "type=bind,src=$CACHE_DIR,dst=/cache" \
  --mount "type=bind,src=$RESULTS_DIR,dst=/results" \
  -e STRATA_BATCH_ABCD=0 -e STRATA_BATCH_ABCD_TRACE=0 \
  docker.io/cassettesgoboom/strata-gfx906@sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29 \
  --engine strata --config /config/config.json --host 0.0.0.0 --port 8080
```

The image was smoke-tested with an external configuration, a short response, and a cached continuation. The exact
model and ROCm requirements for a new machine need local validation. This example uses a user-selected memory
limit and does not assert that any particular model fits it. `--memory-swap` equal to `--memory` disables candidate
swap in Docker's limit model.

AB/CD is **experimental**. For an explicitly scoped four-slot batch-MTP test, set
`STRATA_BATCH_ABCD=1` in the run command and supply a matching batch-four engine configuration. Keep it disabled
for ordinary use until exact native-token and persistent-state parity are demonstrated.
