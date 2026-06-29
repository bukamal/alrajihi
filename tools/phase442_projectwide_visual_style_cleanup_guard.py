#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.projectwide_visual_style_cleanup_contract import phase442_projectwide_visual_style_cleanup_summary


def main() -> int:
    summary = phase442_projectwide_visual_style_cleanup_summary(ROOT)
    if not summary["ready"]:
        print("Phase442 project-wide visual style cleanup guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    legacy = summary["legacy_visual_style_summary"]
    print(
        f"Phase442 project-wide visual style cleanup guard passed: {summary['checks']} checks; "
        f"local style records={legacy['total_local_styles']}; "
        f"legacy_local_style={legacy['counts'].get('legacy_local_style', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
