# -*- coding: utf-8 -*-
"""Write the scenario runtime smoke hook matrix (Phase 272)."""
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.scenarios.scenario_runtime_smoke import (
    run_dry_smoke,
    smoke_coverage_summary,
    smoke_matrix,
    smoke_summary_matrix,
    validate_runtime_smoke_hooks,
)


def _write_csv(path: pathlib.Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    warnings = validate_runtime_smoke_hooks()
    out_dir = ROOT / "tools" / "audit_outputs"
    rows = smoke_matrix()
    summary_rows = smoke_summary_matrix()
    dry_rows = [r.__dict__ for r in run_dry_smoke()]
    _write_csv(out_dir / "scenario_runtime_smoke_matrix.csv", rows)
    _write_csv(out_dir / "scenario_runtime_smoke_summary_matrix.csv", summary_rows)
    _write_csv(out_dir / "scenario_runtime_smoke_dry_run_results.csv", dry_rows)
    summary = smoke_coverage_summary()
    print(f"scenario runtime smoke matrix: {summary['scenario_count']} scenarios / {summary['check_count']} checks -> {out_dir}")
    if warnings:
        print("scenario runtime smoke warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
