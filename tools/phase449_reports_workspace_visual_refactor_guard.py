#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.reports_workspace_visual_refactor_contract import phase449_reports_workspace_visual_refactor_summary


def main() -> int:
    summary = phase449_reports_workspace_visual_refactor_summary(ROOT)
    if not summary["ready"]:
        print("Phase449 reports workspace visual refactor guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase449 reports workspace visual refactor guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
