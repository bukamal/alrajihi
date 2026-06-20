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

from workspace.audit.audit_contract import audit_event_matrix, validate_audit_event_descriptors  # noqa: E402


def main() -> int:
    warnings = validate_audit_event_descriptors()
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "audit_trail_contract_matrix.csv"
    rows = audit_event_matrix()
    fieldnames = [
        "event_key", "audit_scope", "category", "action", "action_code",
        "entity_type", "permission_key", "api_resource", "source_contract",
        "network_mode", "branch_scoped", "required", "severity", "details",
    ]
    with out_file.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"audit events: {len(rows)}")
    print(f"matrix: {out_file}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
