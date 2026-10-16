---
name: benchmark-inference
description: Measure Strata inference on hardware when a benchmark task is requested; distinguish measurement from correctness and report limitations.
---

# Inference benchmark workflow

Use only for an explicitly requested benchmark. Read [`docs/gfx906/CURRENT-STATE.md`](../../../docs/gfx906/CURRENT-STATE.md),
[`docs/gfx906/KNOWN-LIMITATIONS.md`](../../../docs/gfx906/KNOWN-LIMITATIONS.md), and the upstream
[`docs/COMMUNITY_BENCHMARKS.md`](../../../docs/COMMUNITY_BENCHMARKS.md).

The checked-in general benchmark CLI is [`tools/strata_bench.py`](../../../tools/strata_bench.py). It measures a
running or configured Strata server and writes a report. Read its arguments and report format before running; it can
start and stop a server when not given `--url`. Do not run it against production or a live service unless that is
explicitly in scope.

Record exact source and artifact identities, hardware/software, model/configuration, workload, run count, and cache
state. Separate prompt throughput, decode throughput, TTFT, correctness, and failures. Do not generalize the public
dual MI50 32 GB K8/V4 evidence to other configurations. A benchmark does not prove token or session-state parity.
