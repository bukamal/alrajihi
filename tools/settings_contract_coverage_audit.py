#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_FILE = OUT_DIR / "settings_contract_coverage_matrix.csv"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.settings.settings_contract import (  # noqa: E402
    settings_coverage_matrix,
    settings_scope_descriptors,
    uncovered_settings_scopes,
    validate_settings_scope_descriptors,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    warnings = validate_settings_scope_descriptors()
    uncovered = uncovered_settings_scopes()
    rows = list(settings_coverage_matrix())

    with OUT_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = [
            "settings_scope",
            "normalized_scope",
            "covered_by",
            "section_key",
            "service_getter",
            "ui_sections",
            "api_resource",
            "network_mode",
            "required_keys",
            "operation_key_prefixes",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if warnings:
        print("Settings contract warnings:")
        for scope, messages in warnings.items():
            for msg in messages:
                print(f"- {scope}: {msg}")
    if uncovered:
        print("Uncovered settings scopes:")
        for scope in uncovered:
            print(f"- {scope}")
    print(f"settings scopes: {len(rows)}")
    print(f"settings sections: {len(settings_scope_descriptors())}")
    print(f"matrix: {OUT_FILE}")
    return 1 if warnings or uncovered else 0


if __name__ == "__main__":
    raise SystemExit(main())
