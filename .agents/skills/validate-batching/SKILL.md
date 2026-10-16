---
name: validate-batching
description: Validate batching behavior or concurrency claims when explicitly requested, using the checked-in batch test tools and scoped hardware evidence.
---

# Batching validation workflow

Use only when batching behavior or a concurrency claim is explicitly in scope. First read
[`docs/gfx906/CURRENT-STATE.md`](../../../docs/gfx906/CURRENT-STATE.md) and
[`docs/BATCHING.md`](../../../docs/BATCHING.md). Confirm the target build, model, GPU configuration, and exact mode
before selecting a test.

Checked-in tools include [`tools/batch_test.py`](../../../tools/batch_test.py), which compares solo and batched token
sequences for its workload, and [`tools/batch_interleave_test.py`](../../../tools/batch_interleave_test.py), which
exercises interleaved requests. Inspect each tool's arguments and effects before execution; they start an engine and
need a model config and executable. These tools do not automatically validate every batch mode or prove overlap
throughput.

For an AB/CD opt-in or token/state parity claim, record the exact option state and use a matched control. Report token
equality, session-state checks, runtime correctness, observed overlap, and throughput as separate outcomes. Current
public evidence does not close the AB/CD or token/state parity questions.
