#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase444 guard: lazy-loaded pages must be package-safe for Windows."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alrajhi_client.workspace.quality.lazy_page_runtime_packaging_audit import run_audit


def main() -> int:
    summary = run_audit(write_outputs=True)
    if not summary.get("ok"):
        print("Phase444 lazy page runtime packaging guard failed:")
        for err in summary.get("errors", []):
            print(f" - {err}")
        return 1
    checks = int(summary.get("rows", 0))
    print(f"Phase444 lazy page runtime packaging guard passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
