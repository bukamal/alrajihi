#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.unified_list_workspace_visual_template_contract import phase447_unified_list_workspace_visual_template_summary


def main() -> int:
    summary = phase447_unified_list_workspace_visual_template_summary(ROOT)
    if not summary["ready"]:
        print("Phase447 unified list workspace visual template guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase447 unified list workspace visual template guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
