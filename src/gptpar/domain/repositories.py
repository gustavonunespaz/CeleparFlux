from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .models import Macro


class MacroRepository(ABC):
    """Defines persistence contract for macros."""

    @abstractmethod
    def save(self, macro: Macro) -> None:
        """Persist or update a macro."""

    @abstractmethod
    def get(self, name: str) -> Optional[Macro]:
        """Retrieve a macro by its name."""

    @abstractmethod
    def list_all(self) -> Iterable[Macro]:
        """Return all stored macros."""

    @abstractmethod
    def delete(self, name: str) -> None:
        """Remove a macro by its name."""
