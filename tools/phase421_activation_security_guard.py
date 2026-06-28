#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT = ROOT / "tools" / "audit_outputs" / "activation_security_matrix.csv"


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
    from workspace.quality.activation_security_audit import static_security_rows
    from workspace.quality.activation_security_contract import ACTIVATION_SECURITY_CONTRACT

    rows: list[dict[str, str]] = []
    required = [
        "PHASE421_ACTIVATION_SECURITY_HARDENING.md",
        "alrajhi_client/auth/license_security.py",
        "alrajhi_client/auth/activation.py",
        "alrajhi_server/services/security_runtime.py",
        "alrajhi_server/app.py",
        "alrajhi_server/api/debug.py",
        "alrajhi_client/workspace/quality/activation_security_contract.py",
        "alrajhi_client/workspace/quality/activation_security_audit.py",
        "tools/phase421_activation_security_guard.py",
        "tests/test_phase421_activation_security.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase421 file exists")

    for rel in (
        "alrajhi_client/auth/license_security.py",
        "alrajhi_client/auth/activation.py",
        "alrajhi_server/services/security_runtime.py",
        "alrajhi_server/app.py",
        "alrajhi_server/api/debug.py",
        "alrajhi_client/workspace/quality/activation_security_contract.py",
        "alrajhi_client/workspace/quality/activation_security_audit.py",
        "tools/phase421_activation_security_guard.py",
    ):
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", "alrajhi_client/workspace/quality/activation_security_contract.py", ACTIVATION_SECURITY_CONTRACT.get("phase") == 421, "Phase421 contract is declared")
    add(rows, "contract_license_invariants", "contract", "alrajhi_client/workspace/quality/activation_security_contract.py", len(ACTIVATION_SECURITY_CONTRACT.get("license_invariants", ())) >= 6, "license invariants are explicit")
    add(rows, "contract_server_invariants", "contract", "alrajhi_client/workspace/quality/activation_security_contract.py", len(ACTIVATION_SECURITY_CONTRACT.get("server_invariants", ())) >= 5, "server security invariants are explicit")

    for row in static_security_rows(ROOT):
        add(rows, row.key, row.category, row.path, row.ok, row.detail)

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE421_ACTIVATION_SECURITY_HARDENING" in release, "Phase421 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase421_activation_security.py" in release, "Phase421 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "activation_security" in release and "phase=421" in release, "Phase421 release check registered")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase421 activation/security checks: {len(rows)} checks, failures={len(failed)}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
