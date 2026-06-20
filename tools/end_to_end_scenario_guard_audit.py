# -*- coding: utf-8 -*-
"""Write the end-to-end scenario guard matrix (Phase 271)."""
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.scenarios.scenario_guard_contract import (
    scenario_guard_matrix,
    scenario_summary_matrix,
    scenario_coverage_summary,
    validate_scenario_descriptors,
)


def _write_csv(path: pathlib.Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    warnings = validate_scenario_descriptors()
    out_dir = ROOT / "tools" / "audit_outputs"
    rows = scenario_guard_matrix()
    summary_rows = scenario_summary_matrix()
    _write_csv(out_dir / "end_to_end_scenario_guard_matrix.csv", rows)
    _write_csv(out_dir / "end_to_end_scenario_summary_matrix.csv", summary_rows)
    summary = scenario_coverage_summary()
    print(f"end-to-end scenario matrix: {summary['scenario_count']} scenarios / {summary['step_count']} steps -> {out_dir}")
    if warnings:
        print("scenario guard warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
