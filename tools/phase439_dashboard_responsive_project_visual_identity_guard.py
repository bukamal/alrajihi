#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.dashboard_responsive_project_visual_identity_contract import dashboard_responsive_project_visual_identity_summary


def main() -> int:
    summary = dashboard_responsive_project_visual_identity_summary(ROOT)
    if not summary["ready"]:
        print("Phase439 dashboard responsive/project visual identity guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase439 dashboard responsive/project visual identity guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
