#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_CSV = OUT_DIR / "basit_release_candidate_matrix.csv"
OUT_MD = OUT_DIR / "basit_release_candidate_manifest.md"
OUT_JSON = OUT_DIR / "basit_release_candidate_manifest.json"

BASIT_STACK_PHASES = tuple(range(401, 410))

CHECKS = [
    ("phase_doc", "release_candidate", "PHASE410_BASIT_RELEASE_CANDIDATE_FREEZE.md", "Phase 410"),
    ("contract", "release_candidate", "alrajhi_client/workspace/quality/basit_release_candidate_contract.py", "BASIT_RELEASE_CANDIDATE_CONTRACT"),
    ("final_acceptance_contract", "acceptance", "alrajhi_client/workspace/quality/basit_final_acceptance_contract.py", "BASIT_FINAL_ACCEPTANCE_CONTRACT"),
    ("final_acceptance_tool", "acceptance", "tools/phase409_basit_final_acceptance_audit.py", "Phase409 Basit final acceptance audit"),
    ("release_readiness_tool", "release_gate", "tools/release_readiness_gate_audit.py", "release_gate_summary"),
    ("windows_packaging_tool", "release_gate", "tools/windows_runtime_packaging_gate_audit.py", "windows_runtime"),
    ("packaging_guard", "release_gate", "tools/release_packaging_guard.py", "Release packaging guard"),
    ("hidden_imports_guard", "release_gate", "tools/release_hidden_imports_guard.py", "hidden"),
    ("release_gate_doc", "release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE410_BASIT_RELEASE_CANDIDATE_FREEZE"),
    ("release_gate_test", "release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "basit_release_candidate_freeze"),
    ("release_gate_check", "release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "basit_release_candidate_freeze"),
]


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _status(rel: str, needle: str) -> bool:
    return exists(rel) and needle in read(rel)


def _run_tool(rel: str) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, rel],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode == 0, result.stdout.strip()


def _stack_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for phase in BASIT_STACK_PHASES:
        checks = (
            ("doc", bool(list(ROOT.glob(f"PHASE{phase}_*.md"))), f"PHASE{phase}_*.md"),
            ("test", bool(list((ROOT / "tests").glob(f"test_phase{phase}_*.py"))), f"tests/test_phase{phase}_*.py"),
            ("guard", bool(list((ROOT / "tools").glob(f"phase{phase}_*.py"))), f"tools/phase{phase}_*.py"),
        )
        for kind, ok, path in checks:
            rows.append({
                "check": f"phase{phase}_{kind}",
                "category": "basit_stack",
                "path": path,
                "needle": kind,
                "status": "OK" if ok else "FAIL",
                "detail": "",
            })
    return rows


def _write_manifest(rows: list[dict[str, str]], tool_outputs: dict[str, str]) -> None:
    failures = [row for row in rows if row["status"] != "OK"]
    categories: dict[str, tuple[int, int]] = {}
    for row in rows:
        ok, count = categories.get(row["category"], (0, 0))
        categories[row["category"]] = (ok + (1 if row["status"] == "OK" else 0), count + 1)
    payload = {
        "phase": 410,
        "release_candidate": "RC1",
        "status": "READY" if not failures else "NOT_READY",
        "checks": len(rows),
        "passed": len(rows) - len(failures),
        "failed": len(failures),
        "locked_phase_range": [401, 409],
        "categories": {category: {"passed": ok, "total": count} for category, (ok, count) in sorted(categories.items())},
        "tool_outputs": tool_outputs,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Phase410 Basit Release Candidate Manifest",
        "",
        "Release candidate: RC1",
        f"Status: {payload['status']}",
        f"Checks: {payload['passed']}/{payload['checks']} passed",
        "Locked visual stack: Phase401-Phase409",
        "",
        "## Category summary",
        "",
    ]
    for category, data in payload["categories"].items():
        lines.append(f"- {category}: {data['passed']}/{data['total']} OK")
    lines.extend(["", "## Required tools", ""])
    for name, output in tool_outputs.items():
        first_line = output.splitlines()[0] if output else "OK"
        lines.append(f"- {name}: {first_line}")
    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures:
            lines.append(f"- {row['check']}: {row['detail'] or 'missing required marker'}")
    else:
        lines.extend(["", "## Result", "", "READY FOR RELEASE CANDIDATE ZIP", ""])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows: list[dict[str, str]] = []
    for name, category, rel, needle in CHECKS:
        ok = _status(rel, needle)
        rows.append({
            "check": name,
            "category": category,
            "path": rel,
            "needle": needle,
            "status": "OK" if ok else "FAIL",
            "detail": "" if ok else f"missing {needle!r} in {rel}",
        })
    rows.extend(_stack_rows())

    tool_outputs: dict[str, str] = {}
    for name, rel in (
        ("basit_final_acceptance", "tools/phase409_basit_final_acceptance_audit.py"),
        ("release_readiness", "tools/release_readiness_gate_audit.py"),
        ("release_packaging", "tools/release_packaging_guard.py"),
        ("hidden_imports", "tools/release_hidden_imports_guard.py"),
    ):
        ok, output = _run_tool(rel)
        tool_outputs[name] = output
        rows.append({
            "check": f"run_{name}",
            "category": "executable_gates",
            "path": rel,
            "needle": "returncode=0",
            "status": "OK" if ok else "FAIL",
            "detail": output,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "category", "path", "needle", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    _write_manifest(rows, tool_outputs)

    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase410 Basit release candidate freeze failed:")
        for row in failures:
            print(f"- {row['check']}: {row['detail']}")
        print(f"Manifest: {OUT_MD.relative_to(ROOT)}")
        return 1
    print(f"Phase410 Basit release candidate freeze OK ({len(rows)} checks)")
    print(f"Manifest: {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
