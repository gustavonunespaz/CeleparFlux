from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from .models import MacroStep


@dataclass
class RecordingResult:
    start_url: str
    steps: List[MacroStep]
    metadata: Dict[str, object]


class MacroRecorder(ABC):
    """Interface for recording user interactions."""

    @abstractmethod
    def start(self, url: str) -> None:
        """Begin recording interactions for the given URL."""

    @abstractmethod
    def stop(self) -> RecordingResult:
        """Stop recording and return captured steps."""

    @abstractmethod
    def is_recording(self) -> bool:
        """Return whether a recording session is in progress."""


class MacroPlayer(ABC):
    """Interface for executing stored macros."""

    @abstractmethod
    def play(self, steps: List[MacroStep], start_url: str) -> None:
        """Replay the provided macro steps."""
