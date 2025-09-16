from __future__ import annotations

from datetime import datetime, timezone

from gptpar.domain.models import Macro, MacroStep
from gptpar.infrastructure.storage.json_macro_repository import JsonMacroRepository


def _example_macro(name: str) -> Macro:
    return Macro(
        name=name,
        start_url="https://example.com",
        recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        steps=[MacroStep(action="click", selector="body")],
        metadata={"title": "Example"},
    )


def test_save_and_get(tmp_path) -> None:
    storage = tmp_path / "macros.json"
    repository = JsonMacroRepository(storage)

    macro = _example_macro("teste")
    repository.save(macro)

    loaded = repository.get("teste")
    assert loaded is not None
    assert loaded.name == macro.name
    assert loaded.steps[0].action == "click"


def test_list_and_delete(tmp_path) -> None:
    storage = tmp_path / "macros.json"
    repository = JsonMacroRepository(storage)

    repository.save(_example_macro("macro1"))
    repository.save(_example_macro("macro2"))

    macros = list(repository.list_all())
    assert {macro.name for macro in macros} == {"macro1", "macro2"}

    repository.delete("macro1")
    macros_after_delete = list(repository.list_all())
    assert {macro.name for macro in macros_after_delete} == {"macro2"}
