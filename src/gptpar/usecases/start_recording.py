from __future__ import annotations

from ..domain.services import MacroRecorder


class StartMacroRecording:
    """Use case responsible for starting a macro recording."""

    def __init__(self, recorder: MacroRecorder) -> None:
        self._recorder = recorder

    def execute(self, url: str) -> None:
        self._recorder.start(url)
