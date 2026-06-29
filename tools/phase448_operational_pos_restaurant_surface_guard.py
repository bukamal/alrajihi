#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.operational_pos_restaurant_surface_migration_contract import phase448_operational_pos_restaurant_surface_migration_summary


def main() -> int:
    summary = phase448_operational_pos_restaurant_surface_migration_summary(ROOT)
    if not summary["ready"]:
        print("Phase448 operational POS/Restaurant surface migration guard failed:")
        for issue in summary["details"]:
            print(f" - {issue}")
        return 1
    print(f"Phase448 operational POS/Restaurant surface migration guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
