#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_shell_chrome_matrix.csv"

CHECKS = [
    ("contract", "alrajhi_client/workspace/quality/basit_shell_chrome_contract.py", "BASIT_SHELL_CHROME_CONTRACT"),
    ("brand_shell_bg", "alrajhi_client/theme/brand.py", "basit_shell_bg"),
    ("brand_shell_menu", "alrajhi_client/theme/brand.py", "basit_shell_menu_bg"),
    ("brand_shell_active", "alrajhi_client/theme/brand.py", "basit_shell_active_bg"),
    ("nav_phase406", "alrajhi_client/views/main_window.py", "Phase406: Basit-inspired shell navigation chrome"),
    ("nav_property", "alrajhi_client/views/main_window.py", "basitShellChrome"),
    ("action_phase406", "alrajhi_client/shell/unified_action_bar.py", "Phase406: Basit-inspired shared action bar runtime"),
    ("action_property", "alrajhi_client/shell/unified_action_bar.py", "basitShellChrome"),
    ("tabs_phase406", "alrajhi_client/shell/tab_workspace.py", "Phase406: Basit-inspired workspace tab cards"),
    ("tabs_property", "alrajhi_client/shell/tab_workspace.py", "basitShellTabs"),
    ("qss_fallback", "alrajhi_client/theme/qss.py", "Phase406: Basit-inspired shell chrome fallback"),
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    rows = []
    failed = []
    for name, rel, needle in CHECKS:
        ok = needle in read(rel)
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            failed.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if failed:
        print("Phase406 Basit shell chrome guard failed:")
        for issue in failed:
            print("-", issue)
        return 1
    print(f"Phase406 Basit shell chrome guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
