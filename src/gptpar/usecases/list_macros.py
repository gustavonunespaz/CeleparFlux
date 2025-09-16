from __future__ import annotations

from typing import List

from ..domain.models import Macro
from ..domain.repositories import MacroRepository


class ListMacros:
    """Return all macros ordered by recording date."""

    def __init__(self, repository: MacroRepository) -> None:
        self._repository = repository

    def execute(self) -> List[Macro]:
        macros = list(self._repository.list_all())
        macros.sort(key=lambda macro: macro.recorded_at, reverse=True)
        return macros
