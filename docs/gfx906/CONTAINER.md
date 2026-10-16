# Archived gfx906 container

The experimental image is available at
`docker.io/cassettesgoboom/strata-gfx906@sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29`.
The [release record](PROVENANCE.md) identifies the native binary recorded during an archived digest pullback. This
source checkout has not been shown to rebuild that binary. The image contains no model weights; provide a compatible
GGUF, tokenizer/pack, and model-specific data from your own storage. Hardware memory needs depend on the model and
host.

## Run the published image

The published digest's OCI configuration sets the entrypoint to `python3 -m serve.server` and its default arguments
to `--engine strata --config /config/active.json --host 0.0.0.0 --port 8080`. The example below uses that default
command, mounting a prepared server config and model data from the host. It does not run the source tree's setup
entrypoint. The config's engine paths must refer to paths inside the container (for example, `/usr/local/bin/strata`
and files under `/models` or `/data`); use the arguments required by your model pack.

Set these values to absolute paths that exist on the Docker host. `DATA_DIR` must contain the pack/tokenizer files
referenced by your config. `CONFIG_FILE` must be a prepared Strata server JSON config whose container-side paths
match these mounts.

```bash
export GPU0_RENDER=/dev/dri/renderDXXX
export GPU1_RENDER=/dev/dri/renderDYYY
export MODEL_DIR=/path/to/gguf-files
export DATA_DIR=/path/to/model-pack-and-tokenizer
export CONFIG_FILE=/path/to/config.json

docker run --rm --name strata-gfx906-exp \
  --device=/dev/kfd --device="$GPU0_RENDER" --device="$GPU1_RENDER" \
  --ulimit memlock=-1 \
  -p 127.0.0.1:8080:8080 \
  --mount "type=bind,src=$MODEL_DIR,dst=/models,readonly" \
  --mount "type=bind,src=$DATA_DIR,dst=/data,readonly" \
  --mount "type=bind,src=$CONFIG_FILE,dst=/config/active.json,readonly" \
  docker.io/cassettesgoboom/strata-gfx906@sha256:a7527bd8efe2dcdb0a0a7fd6b96761507ce79f9d585ce1649ce5b91158258a29
```

This example keeps the mounted config and model data read-only, binds the API to localhost, and uses the published
image's default server command. The `/dev/dri/renderDXXX` names depend on the host; map the render nodes belonging
to the intended GPUs. The archived smoke used external config and model data with a read-only `/data` mount, but did
not establish compatibility with every model, ROCm installation, or host. Validate those requirements on the target
system. If a model config needs writable runtime data, provide an explicit writable mount for that path.

## Source image distinction

An image built from this checkout has a different entrypoint, `docker-entrypoint.sh`. That source entrypoint reads
setup environment variables such as `FAMILY` and `MODEL`, writes under `/data`, and starts `setup.py`; it does not
forward the published image's server arguments. The published-digest command above must not be copied to an image
built from this source tree.

AB/CD remains experimental and disabled by default. For a separately validated four-slot batch-MTP config,
`-e STRATA_BATCH_ABCD=1` opts in on this archived image. Exact native-token and recurrent-state parity remain open;
the current source checkout has not reproduced this binary.
