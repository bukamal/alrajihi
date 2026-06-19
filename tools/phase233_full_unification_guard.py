# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools" / "phase233_full_unification_audit.py"

spec = importlib.util.spec_from_file_location("phase233_full_unification_audit", AUDIT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)  # type: ignore[union-attr]
report = module.audit()
summary = report.get("summary", {})
if summary.get("high", 0) or summary.get("medium", 0):
    raise AssertionError(json.dumps(summary, ensure_ascii=False) + " — see tools/audit_outputs/phase233_full_unification_audit.json")
print("phase233_full_unification_guard passed")
