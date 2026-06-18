#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 55 heavy UI file elimination guard.

Ensures dashboard/reports are decomposed into smaller components and prevents
regression to monolithic UI files in the high-churn workspace layer.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"

MAX_LINES = 900
REQUIRED_COMPONENTS = [
    "alrajhi_client/views/widgets/dashboard_legacy_components.py",
    "alrajhi_client/views/widgets/reports_phase36_mixin.py",
]
NO_LONGER_ALLOWLISTED = [
    "alrajhi_client/views/widgets/dashboard_widget.py",
    "alrajhi_client/views/widgets/reports_widget.py",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace('\\', '/')


def main() -> int:
    errors: list[str] = []
    for item in REQUIRED_COMPONENTS:
        if not (ROOT / item).exists():
            errors.append(f"missing decomposed component: {item}")
    for item in NO_LONGER_ALLOWLISTED:
        p = ROOT / item
        if not p.exists():
            errors.append(f"missing expected UI entrypoint: {item}")
            continue
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        if len(lines) > MAX_LINES:
            errors.append(f"{item} still too large after Phase 55: {len(lines)} lines")
    for base in (CLIENT / 'views', CLIENT / 'features', CLIENT / 'shell', CLIENT / 'ui'):
        if not base.exists():
            continue
        for path in base.rglob('*.py'):
            try:
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            except SyntaxError as exc:
                errors.append(f"syntax error: {rel(path)}:{exc.lineno}: {exc.msg}")
    dashboard = (ROOT / 'alrajhi_client/views/widgets/dashboard_widget.py').read_text(encoding='utf-8')
    reports = (ROOT / 'alrajhi_client/views/widgets/reports_widget.py').read_text(encoding='utf-8')
    if 'dashboard_legacy_components' not in dashboard:
        errors.append('dashboard_widget must import decomposed dashboard components')
    if 'ReportsPhase36Mixin' not in reports:
        errors.append('reports_widget must use ReportsPhase36Mixin decomposition')
    if errors:
        print('Phase 55 heavy file elimination guard failed:')
        for error in errors:
            print(f' - {error}')
        return 1
    print('Phase 55 heavy file elimination guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
