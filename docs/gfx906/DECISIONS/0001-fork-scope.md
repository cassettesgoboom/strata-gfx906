# Decision 0001: keep the gfx906 fork narrowly scoped

**Status:** Accepted for this documentation foundation
**Date:** 2026-10-16

## Context

Upstream includes an experimental gfx906 wave64 compatibility path and community reports. The fork's current source
base and a published native artifact do not, by themselves, prove that the source can reproduce the artifact or that
current upstream changes have been validated on gfx906. Public GPU evidence is limited to dual MI50 32 GB and K8/V4.

## Decision

Keep this fork focused on reproducible gfx906 source provenance and narrowly stated validation. Preserve inherited
upstream documentation and licensing. Treat GPU support, optimization defaults, AB/CD behavior, and token/state
parity as separate claims requiring evidence. Do not publish private machine details as provenance.

## Consequences

- The upstream base SHA and published artifact SHA prefix are recorded separately.
- Existing upstream build notes are linked rather than copied as proof of a current rebuild.
- Open validation remains explicit in the current-state and limitations pages.
- New reports identify the exact source, artifact, hardware, settings, workload, and limitations.
- No release or default change follows from this decision alone.
