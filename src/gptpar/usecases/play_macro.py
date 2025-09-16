from __future__ import annotations

from ..domain.repositories import MacroRepository
from ..domain.services import MacroPlayer


class PlayMacro:
    """Use case that retrieves and executes a stored macro."""

    def __init__(self, repository: MacroRepository, player: MacroPlayer) -> None:
        self._repository = repository
        self._player = player

    def execute(self, macro_name: str) -> None:
        macro = self._repository.get(macro_name)
        if macro is None:
            raise ValueError(f"Macro '{macro_name}' not found")
        self._player.play(macro.steps, macro.start_url)
