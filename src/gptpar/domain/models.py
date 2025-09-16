from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MacroStep:
    """Represents a single step in a recorded macro."""

    action: str
    selector: Optional[str]
    value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "selector": self.selector,
            "value": self.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MacroStep":
        return cls(
            action=data.get("action"),
            selector=data.get("selector"),
            value=data.get("value"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Macro:
    """Domain entity that stores metadata and steps from a recording."""

    name: str
    start_url: str
    recorded_at: datetime
    steps: List[MacroStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_url": self.start_url,
            "recorded_at": self.recorded_at.isoformat(),
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Macro":
        return cls(
            name=data["name"],
            start_url=data["start_url"],
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
            steps=[MacroStep.from_dict(step) for step in data.get("steps", [])],
            metadata=data.get("metadata", {}),
        )
