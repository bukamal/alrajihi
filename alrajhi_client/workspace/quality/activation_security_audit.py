# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SecurityAuditRow:
    key: str
    category: str
    path: str
    ok: bool
    detail: str


def read(root: Path, rel: str) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def static_security_rows(root: Path) -> list[SecurityAuditRow]:
    license_security = read(root, "alrajhi_client/auth/license_security.py")
    activation = read(root, "alrajhi_client/auth/activation.py")
    server_security = read(root, "alrajhi_server/services/security_runtime.py")
    app = read(root, "alrajhi_server/app.py")
    debug = read(root, "alrajhi_server/api/debug.py")
    rows = [
        SecurityAuditRow("license_security_module", "license", "alrajhi_client/auth/license_security.py", "validate_license_record" in license_security and "verify_signed_license_record" in license_security, "license validation module exists"),
        SecurityAuditRow("license_key_hash", "license", "alrajhi_client/auth/license_security.py", "license_key_hash" in license_security and "key_fingerprint" in license_security, "new records store a key fingerprint"),
        SecurityAuditRow("no_new_raw_key_storage", "license", "alrajhi_client/auth/activation.py", "'key': license_key" not in activation and '"key": license_key' not in activation, "activation no longer writes raw license key into new records"),
        SecurityAuditRow("constant_time_device_compare", "license", "alrajhi_client/auth/license_security.py", "hmac.compare_digest" in license_security, "device binding uses constant-time comparison"),
        SecurityAuditRow("expiration_check", "license", "alrajhi_client/auth/license_security.py", "def is_expired" in license_security and "انتهت صلاحية الترخيص" in license_security, "local expiration check is present"),
        SecurityAuditRow("signed_payload_support", "license", "alrajhi_client/auth/license_security.py", "Ed25519PublicKey" in license_security and "ALRAJHI_LICENSE_PUBLIC_KEY" in license_security, "signed payload verification is supported with external public key"),
        SecurityAuditRow("legacy_unsigned_production_gate", "license", "alrajhi_client/auth/license_security.py", "ALRAJHI_ALLOW_LEGACY_UNSIGNED_LICENSE" in license_security and "is_production_environment" in license_security, "legacy unsigned license policy is environment-gated"),
        SecurityAuditRow("activation_uses_security_builder", "license", "alrajhi_client/auth/activation.py", "build_license_record" in activation and "validate_license_record" in activation, "activation flow uses Phase421 security helpers"),
        SecurityAuditRow("server_security_module", "server", "alrajhi_server/services/security_runtime.py", "diagnostics_enabled" in server_security and "diagnostic_route_required" in server_security, "server diagnostic policy exists"),
        SecurityAuditRow("api_routes_guarded", "server", "alrajhi_server/app.py", "diagnostics_enabled()" in app and "diagnostic_denied_response()" in app and "diagnostic_mode" in app, "/api/routes is hidden unless diagnostics are enabled"),
        SecurityAuditRow("debug_route_guarded", "server", "alrajhi_server/api/debug.py", debug.count("@diagnostic_route_required") >= 2, "debug/monitoring routes require diagnostic mode"),
        SecurityAuditRow("jwt_secret_required", "server", "alrajhi_server/app.py", "ALRAJHI_JWT_SECRET must be set in production" in app, "JWT secret remains mandatory in production"),
    ]
    return rows


def failures(rows: Iterable[SecurityAuditRow]) -> list[SecurityAuditRow]:
    return [row for row in rows if not row.ok]


def summary(root: Path) -> dict[str, object]:
    rows = static_security_rows(root)
    failed = failures(rows)
    categories: dict[str, int] = {}
    for row in rows:
        categories[row.category] = categories.get(row.category, 0) + 1
    return {"rows": len(rows), "failures": len(failed), "categories": categories, "ready": not failed}


__all__ = ["SecurityAuditRow", "failures", "static_security_rows", "summary"]
