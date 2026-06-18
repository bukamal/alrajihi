#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run all Phase 57 release hardening checks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = [
    "tools/release_packaging_guard.py",
    "tools/release_translations_guard.py",
    "tools/release_theme_guard.py",
    "tools/release_hidden_imports_guard.py",
    "tools/unified_printing_guard.py",
]


def main() -> int:
    for rel in CHECKS:
        print(f"==> {rel}")
        completed = subprocess.run([sys.executable, str(ROOT / rel)], cwd=ROOT)
        if completed.returncode != 0:
            return completed.returncode
    print("Release hardening guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
