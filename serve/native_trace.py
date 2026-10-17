"""Small, opt-in bridge helpers for correlating native correctness traces."""
from __future__ import annotations

import inspect
import os
import re


REQUEST_ID = re.compile(r"^[0-9a-f]{32}$")
TRACE_ENV = "STRATA_CORRECTNESS_TRACE"


def enabled() -> bool:
    return os.environ.get(TRACE_ENV) == "1"


def field(request_id: str | None) -> str:
    """Return the optional native protocol field, rejecting absent or unsafe IDs."""
    if request_id is None or not REQUEST_ID.fullmatch(request_id):
        raise ValueError("correctness trace requires a 32-character lowercase hex request ID")
    return f"trace_id={request_id}"


def command(kind: str, max_new: int, sampling_keys: str = "", request_id: str | None = None,
            slot: int | None = None, embeddings: str | None = None) -> str:
    """Build a GEN/GENI/BGEN/BGENI head, preserving the legacy spelling when tracing is off."""
    if kind not in ("GEN", "GENI", "BGEN", "BGENI"):
        raise ValueError("unsupported native generation command")
    if kind.startswith("B") and slot is None:
        raise ValueError("batch command requires a slot")
    if kind.endswith("I") and not embeddings:
        raise ValueError("image command requires an embeddings path")
    trace_key = f" {field(request_id)}" if enabled() else ""
    prefix = f"{kind} {slot} {int(max_new)}" if kind.startswith("B") else f"{kind} {int(max_new)}"
    tail = f" {embeddings}" if kind.endswith("I") else ""
    return f"{prefix}{sampling_keys}{trace_key}{tail}"


def accepts_request_id(method) -> bool:
    """Whether an engine endpoint explicitly accepts the opt-in correlation keyword."""
    try:
        params = inspect.signature(method).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(p.name == "request_id" or p.kind is inspect.Parameter.VAR_KEYWORD for p in params)


class ActiveRequests:
    """CPU-only model of the IDs active in native batch slots."""

    def __init__(self):
        self._active: dict[str, int] = {}

    def begin(self, request_id: str, slot: int) -> None:
        field(request_id)
        if request_id in self._active:
            raise ValueError("duplicate active correctness trace request ID")
        self._active[request_id] = slot

    def complete(self, request_id: str, slot: int, finish: str, produced: int) -> str:
        if self._active.get(request_id) != slot:
            raise ValueError("missing or mismatched correctness trace request ID")
        del self._active[request_id]
        # Deliberately excludes prompt, generated text, and token IDs.
        return (f"strata correctness: request={request_id} slot={slot} state=native_leg_complete "
                f"finish={finish} produced={produced}")
