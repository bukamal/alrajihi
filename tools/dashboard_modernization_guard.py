#!/usr/bin/env python3
"""Guard for Phase 44 dashboard modernization.

Ensures the dashboard uses reusable UI components and pyqtgraph-backed charting
without bypassing the existing service/gateway or unified printing boundaries.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py"
COMPONENTS = ROOT / "alrajhi_client" / "ui" / "dashboard_components.py"


def main() -> int:
    failures: list[str] = []
    for path in (DASHBOARD, COMPONENTS):
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)} parse error: {exc}")
            continue
        if path == COMPONENTS:
            for token in ("class ModernKpiCard", "class DashboardChartPanel", "import pyqtgraph"):
                if token not in source:
                    failures.append(f"dashboard components missing {token}")
        if path == DASHBOARD:
            for token in ("ModernKpiCard", "DashboardChartPanel", "_build_kpi_grid", "_refresh_kpis"):
                if token not in source:
                    failures.append(f"dashboard widget missing {token}")
            forbidden = ("sqlite3", "DatabaseConnection", ".execute(", ".query(", "printing_service.print_")
            for token in forbidden:
                if token in source:
                    failures.append(f"dashboard widget must not contain {token}")
    if failures:
        print("Dashboard modernization guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("Dashboard modernization guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
