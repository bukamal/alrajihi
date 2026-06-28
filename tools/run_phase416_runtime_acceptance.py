# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.runtime.runtime_acceptance_harness import (  # noqa: E402
    pyqt_runtime_status,
    run_all_available_runtime_probes,
    write_scenario_matrix,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase416 Qt runtime acceptance probes when PyQt5 is available.")
    parser.add_argument("--output-dir", default="tools/audit_outputs/runtime_acceptance", help="Directory for widget trees, screenshots and probe JSON files.")
    parser.add_argument("--matrix-only", action="store_true", help="Write the scenario matrix without opening Qt windows.")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    matrix = write_scenario_matrix(out / "runtime_acceptance_scenario_matrix.csv")
    if args.matrix_only:
        payload = {"matrix": str(matrix), "pyqt_status": pyqt_runtime_status()}
    else:
        payload = run_all_available_runtime_probes(output_dir=out)
        payload["matrix"] = str(matrix)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    # The CLI exits 0 when PyQt is unavailable because that is an environment
    # limitation, not a source failure. Probe failures are represented inside JSON.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
