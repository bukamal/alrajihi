#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.runtime_layout_reconstruction_contract import phase454_runtime_layout_reconstruction_summary

if __name__ == "__main__":
    summary = phase454_runtime_layout_reconstruction_summary(ROOT)
    if not summary["ready"]:
        print("Phase454 Runtime layout reconstruction guard failed:")
        for detail in summary["details"]:
            print(f" - {detail}")
        raise SystemExit(1)
    print(f"Phase454 Runtime layout reconstruction guard passed: {summary['checks']} checks")
