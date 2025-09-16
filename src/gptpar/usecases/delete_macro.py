from __future__ import annotations

from ..domain.repositories import MacroRepository


class DeleteMacro:
    """Use case that removes a stored macro."""

    def __init__(self, repository: MacroRepository) -> None:
        self._repository = repository

    def execute(self, macro_name: str) -> None:
        self._repository.delete(macro_name)
