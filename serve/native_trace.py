"""Small, opt-in bridge helpers for correlating native correctness traces."""
from __future__ import annotations

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
        return f"strata correctness: request={request_id} slot={slot} state=complete finish={finish} produced={produced}"
