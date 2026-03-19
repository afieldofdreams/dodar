"""UI-agnostic progress tracking via callbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    ITEM_START = "item_start"
    ITEM_COMPLETE = "item_complete"
    ITEM_ERROR = "item_error"
    RUN_COMPLETE = "run_complete"
    RUN_ERROR = "run_error"


@dataclass
class ProgressEvent:
    type: EventType
    scenario_id: str = ""
    model: str = ""
    condition: str = ""
    completed: int = 0
    total: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: str = ""
    summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type.value}
        if self.scenario_id:
            d["scenario_id"] = self.scenario_id
        if self.model:
            d["model"] = self.model
        if self.condition:
            d["condition"] = self.condition
        d["progress"] = {"completed": self.completed, "total": self.total}
        if self.tokens_used:
            d["tokens_used"] = self.tokens_used
        if self.cost_usd:
            d["cost_usd"] = self.cost_usd
        if self.error:
            d["error"] = self.error
        if self.summary:
            d["summary"] = self.summary
        return d


class ProgressTracker:
    """Distributes progress events to registered listeners."""

    def __init__(self) -> None:
        self._callbacks: list[Callable[[ProgressEvent], None]] = []

    def add_listener(self, callback: Callable[[ProgressEvent], None]) -> None:
        self._callbacks.append(callback)

    def remove_listener(self, callback: Callable[[ProgressEvent], None]) -> None:
        self._callbacks = [cb for cb in self._callbacks if cb is not callback]

    def emit(self, event: ProgressEvent) -> None:
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                pass  # don't let a bad listener break the executor
