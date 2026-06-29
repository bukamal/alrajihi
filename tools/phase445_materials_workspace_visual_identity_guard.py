#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.materials_workspace_visual_identity_migration_contract import phase445_materials_workspace_visual_identity_summary


def main() -> int:
    summary = phase445_materials_workspace_visual_identity_summary(ROOT)
    if not summary["ready"]:
        print("Phase445 materials workspace visual identity guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase445 materials workspace visual identity guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
