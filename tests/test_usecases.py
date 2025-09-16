from __future__ import annotations

from datetime import datetime, timezone

from gptpar.domain.models import Macro, MacroStep
from gptpar.domain.repositories import MacroRepository
from gptpar.domain.services import MacroRecorder, RecordingResult
from gptpar.usecases.play_macro import PlayMacro
from gptpar.usecases.start_recording import StartMacroRecording
from gptpar.usecases.stop_recording import StopMacroRecording


class InMemoryRepository(MacroRepository):
    def __init__(self) -> None:
        self._storage: dict[str, Macro] = {}

    def save(self, macro: Macro) -> None:
        self._storage[macro.name] = macro

    def get(self, name: str) -> Macro | None:
        return self._storage.get(name)

    def list_all(self):  # type: ignore[override]
        return list(self._storage.values())

    def delete(self, name: str) -> None:
        self._storage.pop(name, None)


class FakeRecorder(MacroRecorder):
    def __init__(self) -> None:
        self.started_with: str | None = None
        self._is_recording = False

    def start(self, url: str) -> None:
        self.started_with = url
        self._is_recording = True

    def stop(self) -> RecordingResult:
        self._is_recording = False
        return RecordingResult(
            start_url="https://example.com",
            steps=[MacroStep(action="click", selector="body")],
            metadata={"title": "Example"},
        )

    def is_recording(self) -> bool:
        return self._is_recording


class FakePlayer:
    def __init__(self) -> None:
        self.played = False

    def play(self, steps, start_url):
        self.played = True


def test_start_and_stop_recording_usecases() -> None:
    recorder = FakeRecorder()
    repository = InMemoryRepository()

    start = StartMacroRecording(recorder)
    stop = StopMacroRecording(recorder, repository)

    start.execute("https://example.com")
    macro = stop.execute("macro_teste")

    assert macro.name == "macro_teste"
    assert repository.get("macro_teste") is not None
    assert recorder.started_with == "https://example.com"


def test_play_macro_usecase() -> None:
    repository = InMemoryRepository()
    repository.save(
        Macro(
            name="macro",
            start_url="https://example.com",
            recorded_at=datetime.now(timezone.utc),
            steps=[MacroStep(action="click", selector="body")],
            metadata={},
        )
    )
    fake_player = FakePlayer()

    play = PlayMacro(repository, fake_player)
    play.execute("macro")

    assert fake_player.played is True
