#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.operational.operational_shell_contract import (  # noqa: E402
    operational_shell_matrix,
    validate_operational_descriptors,
)

OUTPUT = ROOT / "tools" / "audit_outputs" / "operational_shell_contract_matrix.csv"


def main() -> int:
    warnings = validate_operational_descriptors()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = operational_shell_matrix()
    fieldnames = list(rows[0].keys()) if rows else []
    with OUTPUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if warnings:
        print("Operational shell contract warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    print(f"Operational shell contract matrix written: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
