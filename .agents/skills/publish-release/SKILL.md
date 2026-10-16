---
name: publish-release
description: Prepare release evidence for this repository only when a release is explicitly requested; do not assume a checked-in publishing CLI or publish without explicit authorization.
---

# Release preparation

Use only for an explicit release task. Begin with [`docs/gfx906/START-HERE.md`](../../../docs/gfx906/START-HERE.md),
[`docs/gfx906/CURRENT-STATE.md`](../../../docs/gfx906/CURRENT-STATE.md), and
[`docs/gfx906/KNOWN-LIMITATIONS.md`](../../../docs/gfx906/KNOWN-LIMITATIONS.md). Confirm the intended source revision,
artifact identity, version, release notes, and validation evidence before preparing release material.

Do not infer a publishing capability from this skill. No checked-in `tools/release` CLI was found in the inspected
source paths. Inspect the repository's current release workflow and documentation as part of a release task. If the
user has already authorized the exact release action, follow that authorization without asking again. If the process
or scope is still unclear, prepare a reviewable proposal and stop before the unclear action. Never claim that the
native artifact is reproducible from source without a demonstrated rebuild. Preserve the MIT license and upstream
notices in redistributed artifacts.
