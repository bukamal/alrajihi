# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workspace.lists.list_workspace_contract import (  # noqa: E402
    list_workspace_matrix,
    validate_list_descriptors,
)


def main() -> int:
    rows = list_workspace_matrix()
    warnings = validate_list_descriptors()
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "list_workspace_contract_matrix.csv"
    with out_file.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(f"List workspaces: {len(rows)}")
    print(f"Matrix: {out_file}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    print("No list workspace contract warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
