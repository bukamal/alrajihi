# -*- coding: utf-8 -*-
"""Phase435 login-to-main-window startup timeline profiler.

This module is deliberately Qt-free so it can be used by CI guards and by the
runtime before/after QApplication objects are visible.  It records startup and
post-login milestones and writes JSON/CSV audit artifacts for diagnosing long
waits between accepting LoginDialog and showing MainWindow.
"""
from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


PHASE435_TIMELINE_MARKER = "phase435_login_to_mainwindow_transition_profiler"


@dataclass(frozen=True)
class StartupTimelineEvent:
    name: str
    elapsed_ms: int
    delta_ms: int
    category: str = "runtime"
    detail: str = ""


class StartupTimelineProfiler:
    """Small runtime profiler for the login-to-main transition.

    The profiler is intentionally passive: it never sleeps, never imports PyQt,
    and never changes application flow.  UI code can call ``mark`` around heavy
    operations and export the resulting timeline at the end of startup.
    """

    marker = PHASE435_TIMELINE_MARKER

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self._last = self._start
        self._events: List[StartupTimelineEvent] = []
        self.context: Dict[str, str] = {}
        self.mark("app_start", "Application entry point reached", category="startup")

    def set_context(self, **values: object) -> None:
        for key, value in values.items():
            if value is not None:
                self.context[str(key)] = str(value)

    def mark(self, name: str, detail: str = "", *, category: str = "runtime") -> StartupTimelineEvent:
        now = time.perf_counter()
        event = StartupTimelineEvent(
            name=name,
            elapsed_ms=int((now - self._start) * 1000),
            delta_ms=int((now - self._last) * 1000),
            category=category,
            detail=detail,
        )
        self._events.append(event)
        self._last = now
        return event

    @property
    def events(self) -> List[StartupTimelineEvent]:
        return list(self._events)

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)

    def summary(self) -> Dict[str, object]:
        login_accepted = self._find("login_accepted")
        main_shown = self._find("main_window_shown")
        post_login_ms: Optional[int] = None
        if login_accepted and main_shown:
            post_login_ms = max(0, main_shown.elapsed_ms - login_accepted.elapsed_ms)
        return {
            "marker": self.marker,
            "events": len(self._events),
            "total_elapsed_ms": self.elapsed_ms(),
            "post_login_to_main_ms": post_login_ms,
            "context": dict(self.context),
        }

    def _find(self, name: str) -> Optional[StartupTimelineEvent]:
        for event in self._events:
            if event.name == name:
                return event
        return None

    def export(self, output_dir: str | Path = "tools/audit_outputs") -> Dict[str, Path]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        json_path = out / "startup_timeline.json"
        csv_path = out / "startup_timeline.csv"
        payload = {
            "summary": self.summary(),
            "events": [asdict(event) for event in self._events],
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["name", "elapsed_ms", "delta_ms", "category", "detail"])
            writer.writeheader()
            for event in self._events:
                writer.writerow(asdict(event))
        return {"json": json_path, "csv": csv_path}
