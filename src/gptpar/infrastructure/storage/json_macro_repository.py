from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Iterable, List, Optional

from ...domain.models import Macro
from ...domain.repositories import MacroRepository


class JsonMacroRepository(MacroRepository):
    """Stores macros in a JSON file."""

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._lock = Lock()
        self._ensure_file()

    def save(self, macro: Macro) -> None:
        with self._lock:
            data = self._read_all()
            existing_index = next((i for i, item in enumerate(data) if item["name"] == macro.name), None)
            serialized = macro.to_dict()
            if existing_index is not None:
                data[existing_index] = serialized
            else:
                data.append(serialized)
            self._write_all(data)

    def get(self, name: str) -> Optional[Macro]:
        with self._lock:
            for item in self._read_all():
                if item["name"] == name:
                    return Macro.from_dict(item)
        return None

    def list_all(self) -> Iterable[Macro]:
        with self._lock:
            return [Macro.from_dict(item) for item in self._read_all()]

    def delete(self, name: str) -> None:
        with self._lock:
            data = [item for item in self._read_all() if item["name"] != name]
            self._write_all(data)

    def _ensure_file(self) -> None:
        if not self._storage_path.exists():
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_all([])

    def _read_all(self) -> List[dict]:
        with self._storage_path.open("r", encoding="utf-8") as fp:
            try:
                return json.load(fp)
            except json.JSONDecodeError:
                return []

    def _write_all(self, data: List[dict]) -> None:
        with self._storage_path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
