#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_printing_surface_matrix.csv"

CHECKS = [
    ("contract", "alrajhi_client/workspace/quality/basit_printing_surface_contract.py", "BASIT_PRINTING_SURFACE_CONTRACT"),
    ("phase_doc", "PHASE408_BASIT_PRINTING_SURFACE.md", "PHASE408"),
    ("token_bridge", "alrajhi_client/printing/print_templates.py", "def _basit_print_tokens"),
    ("phase_marker", "alrajhi_client/printing/print_templates.py", "Phase408: Basit-inspired print/export surface"),
    ("theme_import", "alrajhi_client/printing/print_templates.py", "from theme.brand import LIGHT_TOKENS, DARK_TOKENS"),
    ("blue_accent", "alrajhi_client/printing/print_templates.py", "accent = basit['blue']"),
    ("yellow_header", "alrajhi_client/printing/print_templates.py", "border-top: 6px solid {basit['yellow']}"),
    ("yellow_badge", "alrajhi_client/printing/print_templates.py", "background: {basit['yellow']}; color: {basit['category_text']}"),
    ("table_header", "alrajhi_client/printing/print_templates.py", "background: {basit['table_header_bg']}"),
    ("red_total", "alrajhi_client/printing/print_templates.py", ".totals-table tr.final td {{ background: {basit['red']}"),
    ("thermal_kept", "alrajhi_client/printing/print_templates.py", ".thermal80 .sheet, .thermal58 .sheet"),
    ("release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "basit_printing_surface"),
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    rows = []
    failures = []
    for name, rel, needle in CHECKS:
        ok = needle in read(rel)
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            failures.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if failures:
        print("Phase408 Basit printing surface guard failed:")
        for failure in failures:
            print("-", failure)
        return 1
    print(f"Phase408 Basit printing surface guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
