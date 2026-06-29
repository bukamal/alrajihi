#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.legacy_visual_style_sweep_contract import phase440_visual_sweep_summary


def main() -> int:
    summary = phase440_visual_sweep_summary(ROOT)
    if not summary["ready"]:
        print("Phase440 legacy visual style sweep guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    legacy = summary["legacy"]
    windows = summary["windows"]
    print(
        f"Phase440 legacy visual style sweep guard passed: {summary['checks']} checks; "
        f"local style records={legacy['total_local_styles']}; windows rows={windows['rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
