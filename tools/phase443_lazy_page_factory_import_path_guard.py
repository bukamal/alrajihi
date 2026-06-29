#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.lazy_page_factory_import_path_contract import phase443_lazy_page_factory_import_path_summary


def main() -> int:
    summary = phase443_lazy_page_factory_import_path_summary(ROOT)
    if not summary["ready"]:
        print("Phase443 lazy page factory import path guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(
        f"Phase443 lazy page factory import path guard passed: {summary['checks']} checks; "
        f"lazy factories={summary['spec_count']}; legacy short specs=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
