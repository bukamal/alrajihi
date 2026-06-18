#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate theme/QSS assets used by modern workspace UI."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

REQUIRED_TOKENS = ["bg_window", "bg_panel", "text_primary", "text_secondary", "border", "success", "warning", "danger"]
REQUIRED_QSS_SNIPPETS = ["QMainWindow", "QTabWidget", "QTableView", "QPushButton", "QLineEdit"]


def main() -> int:
    errors: list[str] = []
    try:
        from theme.brand import get_tokens
        from theme.qss import build_global_qss
    except Exception as exc:
        print(f"Release theme guard failed: cannot import theme modules: {exc}")
        return 1
    colors = get_tokens('light')
    for token in REQUIRED_TOKENS:
        if token not in colors:
            errors.append(f"Missing theme token: {token}")
    try:
        qss = build_global_qss(colors)
    except Exception as exc:
        errors.append(f"build_global_qss failed: {exc}")
        qss = ""
    for snippet in REQUIRED_QSS_SNIPPETS:
        if snippet not in qss:
            errors.append(f"QSS missing selector/snippet: {snippet}")
    if errors:
        print("Release theme guard failed:")
        for e in errors:
            print(f" - {e}")
        return 1
    print("Release theme guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
