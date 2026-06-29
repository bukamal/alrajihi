#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.unified_document_editor_visual_template_contract import phase450_unified_document_editor_visual_template_summary


def main() -> int:
    summary = phase450_unified_document_editor_visual_template_summary(ROOT)
    if not summary["ready"]:
        print("Phase450 unified document editor visual template guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase450 unified document editor visual template guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
