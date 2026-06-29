#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 435 login-to-main transition profiler/overlay."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_to_main_transition_contract import (  # noqa: E402
    login_to_main_transition_matrix,
    login_to_main_transition_summary,
)


def main() -> int:
    rows = login_to_main_transition_matrix(ROOT)
    summary = login_to_main_transition_summary(ROOT)
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "login_to_main_transition_matrix.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    issues = [row for row in rows if row.get("status") != "pass"]
    if issues:
        print(json.dumps({"summary": summary, "issues": issues[:14]}, ensure_ascii=False, indent=2))
        return 1
    print(f"Phase 435 login-to-main transition guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
