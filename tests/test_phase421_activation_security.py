# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import datetime as dt
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))
SERVER_PARENT = ROOT
if str(SERVER_PARENT) not in sys.path:
    sys.path.insert(0, str(SERVER_PARENT))


def load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase421_contract_summary_ready():
    module = load_module("alrajhi_client/workspace/quality/activation_security_contract.py", "phase421_contract")
    summary = module.contract_summary()
    assert summary["phase"] == 421
    assert summary["license_invariant_count"] >= 6
    assert summary["server_invariant_count"] >= 5


def test_phase421_license_record_hashes_key_and_validates_expiration(monkeypatch):
    security = load_module("alrajhi_client/auth/license_security.py", "phase421_license_security")
    monkeypatch.delenv("ALRAJHI_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    record = security.build_license_record(
        license_key="ABCD-SECRET-KEY",
        device_id="device-1",
        server_result={"expirationDate": "2099-01-01T00:00:00+00:00"},
    )
    assert record["license_key_hash"] == security.key_fingerprint("ABCD-SECRET-KEY")
    assert "key" not in record
    ok, message = security.validate_license_record(record, expected_device="device-1")
    assert ok, message
    expired = dict(record, expiration="2000-01-01T00:00:00+00:00")
    ok, message = security.validate_license_record(expired, expected_device="device-1", now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
    assert not ok
    assert "صلاحية" in message


def test_phase421_legacy_unsigned_license_rejected_in_production(monkeypatch):
    security = load_module("alrajhi_client/auth/license_security.py", "phase421_license_security_prod")
    monkeypatch.setenv("ALRAJHI_ENV", "production")
    monkeypatch.delenv("ALRAJHI_ALLOW_LEGACY_UNSIGNED_LICENSE", raising=False)
    assert security.is_production_environment() is True
    assert security.allow_legacy_unsigned_license() is False
    record = {"device": "device-1", "legacy_unsigned": True, "signed": False}
    ok, message = security.validate_license_record(record, expected_device="device-1")
    assert not ok
    assert "غير موق" in message


def test_phase421_feature_claim_mismatch_is_rejected(monkeypatch):
    security = load_module("alrajhi_client/auth/license_security.py", "phase421_license_security_feature")
    monkeypatch.delenv("ALRAJHI_ENV", raising=False)
    record = {"device": "device-1", "feature": "restaurant", "signed": False, "legacy_unsigned": True}
    ok, message = security.validate_license_record(record, expected_device="device-1", expected_feature="cafe")
    assert not ok
    assert "cafe" in message


def test_phase421_server_diagnostics_policy(monkeypatch):
    policy = load_module("alrajhi_server/services/security_runtime.py", "phase421_server_security")
    monkeypatch.setenv("ALRAJHI_ENV", "production")
    monkeypatch.delenv("ALRAJHI_ENABLE_DIAGNOSTICS", raising=False)
    assert policy.is_production_environment() is True
    assert policy.diagnostics_enabled() is False
    monkeypatch.setenv("ALRAJHI_ENABLE_DIAGNOSTICS", "1")
    assert policy.diagnostics_enabled() is True


def test_phase421_static_audit_has_no_failures():
    from workspace.quality.activation_security_audit import failures, static_security_rows

    rows = static_security_rows(ROOT)
    assert len(rows) >= 10
    failed = failures(rows)
    assert not failed, [(row.key, row.detail) for row in failed]


def test_phase421_guard_generates_matrix():
    result = subprocess.run([sys.executable, "tools/phase421_activation_security_guard.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/activation_security_matrix.csv"
    assert matrix.exists()
    with matrix.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 30
    assert all(row["status"] == "OK" for row in rows)
