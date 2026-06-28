#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT = ROOT / "tools" / "audit_outputs" / "i18n_rtl_quality_matrix.csv"
COVERAGE_OUT = ROOT / "tools" / "audit_outputs" / "i18n_rtl_quality_coverage.json"
USAGE_OUT = ROOT / "tools" / "audit_outputs" / "i18n_rtl_translation_key_usage.json"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parses(rel: str) -> bool:
    try:
        ast.parse(read(rel))
        return True
    except SyntaxError:
        return False


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({"key": key, "category": category, "path": path, "status": "OK" if ok else "FAIL", "detail": detail})


def main() -> int:
    from workspace.quality.i18n_rtl_quality_audit import (
        code_translation_key_usage,
        coverage_summary,
        failures,
        i18n_rtl_quality_rows,
    )
    from workspace.quality.i18n_rtl_quality_contract import I18N_RTL_QUALITY_CONTRACT, contract_summary

    rows: list[dict[str, str]] = []
    required = [
        "PHASE422_I18N_RTL_QUALITY_GATE.md",
        "alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py",
        "alrajhi_client/workspace/quality/i18n_rtl_quality_audit.py",
        "alrajhi_client/i18n/translator.py",
        "alrajhi_client/ui/table_direction_policy.py",
        "alrajhi_client/views/main_window.py",
        "alrajhi_client/views/widgets/settings_widget.py",
        "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py",
        "tools/phase422_i18n_rtl_quality_guard.py",
        "tests/test_phase422_i18n_rtl_quality.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase422 file exists")

    for rel in (
        "alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py",
        "alrajhi_client/workspace/quality/i18n_rtl_quality_audit.py",
        "alrajhi_client/i18n/translator.py",
        "alrajhi_client/ui/table_direction_policy.py",
        "tools/phase422_i18n_rtl_quality_guard.py",
    ):
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    summary = contract_summary()
    add(rows, "contract_phase", "contract", "alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py", summary["phase"] == 422, "Phase422 contract is declared")
    add(rows, "contract_supported_languages", "contract", "alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py", tuple(I18N_RTL_QUALITY_CONTRACT["supported_languages"]) == ("ar", "de", "en", "fr"), "supported language set is explicit")
    add(rows, "contract_critical_keys", "contract", "alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py", int(summary["critical_key_count"]) >= 35, "critical UI/print/runtime keys are explicit")
    add(rows, "contract_runtime_invariants", "contract", "alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py", int(summary["runtime_direction_invariant_count"]) >= 5, "runtime direction invariants are explicit")

    audit_rows = i18n_rtl_quality_rows(ROOT)
    for row in audit_rows:
        add(rows, row.key, row.category, row.path, row.ok, row.detail)

    usage = code_translation_key_usage(ROOT)
    coverage = coverage_summary(ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)
    COVERAGE_OUT.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")
    USAGE_OUT.write_text(json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    release_rows: list[dict[str, str]] = []
    add(release_rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE422_I18N_RTL_QUALITY_GATE" in release, "Phase422 doc registered")
    add(release_rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase422_i18n_rtl_quality.py" in release, "Phase422 test registered")
    add(release_rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "i18n_rtl_quality" in release and "phase=422" in release, "Phase422 release check registered")
    # Append release rows to matrix after writing primary audit rows, then rewrite once.
    rows.extend(release_rows)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase422 i18n/RTL quality checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Coverage summary: {COVERAGE_OUT}")
    print(f"Literal key usage: {USAGE_OUT}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
