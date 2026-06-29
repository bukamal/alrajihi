#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.dialogs_modal_windows_visual_unification_contract import phase452_dialogs_modal_windows_visual_unification_summary


def main() -> int:
    summary = phase452_dialogs_modal_windows_visual_unification_summary(ROOT)
    if not summary["ready"]:
        print("Phase452 dialogs/modal visual unification guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase452 dialogs/modal visual unification guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
