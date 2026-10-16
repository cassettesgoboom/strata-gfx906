# gfx906 benchmark evidence format

`schema-v1.json` describes one benchmark record. It is model and harness agnostic: record the model, exact source and
build identity, hardware, workload, actual output, cache evidence, optional native occupancy and measured units.
Keep raw client token events and native logs alongside the record when publishing a GPU result; use relative
`source_ref` values that resolve in the shared evidence bundle. Never put prompt text, credentials, private host
paths or raw private logs in a public report.

Run `python tools/gfx906.py bench-validate RECORD.json` and
`python tools/gfx906.py report RECORD.json` from the repository root. These commands check internal consistency;
they do **not** open or authenticate referenced raw logs and do not prove the report came from a GPU. Independent
review must verify those artifacts, source/build identity, and the claimed metrics before calling a run validated.
The committed synthetic fixture is deliberately rejected as real run evidence. The CPU test suite and
GitHub-hosted workflow check that rejection and the validator's false-positive cases without privileged devices or
model weights. Run `python tools/gfx906.py test-cpu` locally before submitting a PR.

For cached performance, declare `cache_state=cached` only when the native reused-token count is at least 98% of
the exact tokenized prompt. The validator requires a prompt hash and reused/fresh counts. For a strict concurrent
decode claim, include client output envelopes and native slot/window evidence covering their common interval. An
overlap of HTTP requests alone is insufficient. A natural EOS below the output cap can be recorded as a valid
completed response, but it cannot satisfy a sustained 512-token claim.

Keep capacity, performance and correctness outcomes separate. A throughput or cached-continuation result does not
establish exact token-ID or recurrent-state parity. Historical observations and limitations are indexed in
[`docs/gfx906/EVIDENCE.md`](../../docs/gfx906/EVIDENCE.md).
