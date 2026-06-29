#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.windows_runtime_visual_acceptance_corrections_contract import phase453_windows_runtime_visual_acceptance_corrections_summary

if __name__ == "__main__":
    summary = phase453_windows_runtime_visual_acceptance_corrections_summary(ROOT)
    if not summary["ready"]:
        print("Phase453 Windows runtime visual acceptance corrections guard failed:")
        for detail in summary["details"]:
            print(f" - {detail}")
        raise SystemExit(1)
    print(f"Phase453 Windows runtime visual acceptance corrections guard passed: {summary['checks']} checks")
