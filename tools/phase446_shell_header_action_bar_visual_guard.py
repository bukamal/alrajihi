#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.shell_header_action_bar_visual_consolidation_contract import phase446_shell_header_action_bar_visual_consolidation_summary


def main() -> int:
    summary = phase446_shell_header_action_bar_visual_consolidation_summary(ROOT)
    if not summary["ready"]:
        print("Phase446 shell header/action bar visual guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase446 shell header/action bar visual guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
