#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "alrajhi_client") not in sys.path:
    sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.targeted_screen_rebuild_contract import phase455_targeted_screen_rebuild_summary


def main() -> int:
    summary = phase455_targeted_screen_rebuild_summary(ROOT)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
