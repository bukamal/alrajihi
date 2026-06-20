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

from workspace.sync.offline_sync_contract import offline_sync_matrix, validate_offline_sync_descriptors  # noqa: E402


def main() -> int:
    warnings = validate_offline_sync_descriptors()
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "offline_sync_contract_matrix.csv"
    rows = offline_sync_matrix()
    fieldnames = [
        "surface_key", "surface_family", "document_type", "api_resource", "network_mode",
        "offline_policy", "queueable", "allowed_methods", "queueable_prefixes",
        "conflict_policy", "replay_priority", "idempotency_key", "branch_required",
        "audit_required", "settings_scope", "permission_keys", "source_contract", "notes",
    ]
    with out_file.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"offline sync surfaces: {len(rows)}")
    print(f"matrix: {out_file}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
