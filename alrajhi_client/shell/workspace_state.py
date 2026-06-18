# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

from PyQt5.QtCore import QStandardPaths


@dataclass(frozen=True)
class WorkspaceEntry:
    tab_id: str
    title: str
    icon_name: str = "fa5s.folder-open"
    singleton: bool = True


class WorkspaceStateStore:
    """Persist light shell state: recent pages, favorite pages, and restorable tabs."""

    def __init__(self, filename: str = "workspace_state.json") -> None:
        base = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        if not base:
            base = str(Path.home() / ".alrajhi_gateway")
        self.path = Path(base) / filename

    def _read(self) -> dict:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
        return {}

    def _write(self, data: dict) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def recent(self) -> List[WorkspaceEntry]:
        items = self._read().get("recent", [])
        return [WorkspaceEntry(**item) for item in items if isinstance(item, dict) and item.get("tab_id")]

    def favorites(self) -> List[str]:
        values = self._read().get("favorites", [])
        return [str(v) for v in values if v]

    def session(self) -> List[WorkspaceEntry]:
        items = self._read().get("session", [])
        return [WorkspaceEntry(**item) for item in items if isinstance(item, dict) and item.get("tab_id")]

    def set_favorites(self, tab_ids: Iterable[str]) -> None:
        data = self._read()
        data["favorites"] = [str(tab_id) for tab_id in tab_ids if tab_id]
        self._write(data)

    def add_recent(self, entry: WorkspaceEntry, limit: int = 10) -> None:
        data = self._read()
        current = [item for item in data.get("recent", []) if isinstance(item, dict)]
        current = [item for item in current if item.get("tab_id") != entry.tab_id]
        current.insert(0, asdict(entry))
        data["recent"] = current[:limit]
        self._write(data)

    def save_session(self, entries: Iterable[WorkspaceEntry]) -> None:
        data = self._read()
        # Keep only singleton pages for safe restore. Document tabs can be restored later
        # once every document type has stable reopen-by-id support.
        data["session"] = [asdict(entry) for entry in entries if entry.singleton]
        self._write(data)
