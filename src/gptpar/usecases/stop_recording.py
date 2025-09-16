from __future__ import annotations

from datetime import datetime, timezone

from ..domain.models import Macro
from ..domain.repositories import MacroRepository
from ..domain.services import MacroRecorder


class StopMacroRecording:
    """Use case responsible for finishing a recording and persisting the macro."""

    def __init__(self, recorder: MacroRecorder, repository: MacroRepository) -> None:
        self._recorder = recorder
        self._repository = repository

    def execute(self, macro_name: str) -> Macro:
        result = self._recorder.stop()
        macro = Macro(
            name=macro_name,
            start_url=result.start_url,
            recorded_at=datetime.now(timezone.utc),
            steps=result.steps,
            metadata=result.metadata,
        )
        self._repository.save(macro)
        return macro
