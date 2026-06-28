# -*- coding: utf-8 -*-
"""Phase 421 activation/license security helpers.

The desktop client historically stored a device-bound encrypted activation blob.
Phase 421 keeps that compatibility for non-production deployments, but introduces
an explicit validation boundary for signed license payloads, expiration checks,
feature claims, and raw-license-key minimization.
"""
from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import hmac
import json
import os
from typing import Any, Mapping, Optional, Tuple

try:  # Ed25519 is preferred when the activation service returns signed payloads.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
except Exception:  # pragma: no cover - packaging fallback
    Ed25519PublicKey = None  # type: ignore[assignment]
    InvalidSignature = Exception  # type: ignore[assignment]

LICENSE_SCHEMA_VERSION = 2
SIGNED_LICENSE_ALGORITHMS = ("ed25519", "ed25519-sha512")
PRODUCTION_ENV_VALUES = {"production", "prod", "release"}


def is_production_environment() -> bool:
    """Return True when unsigned legacy licenses must not be trusted."""
    return any(
        str(os.environ.get(name, "")).strip().lower() in PRODUCTION_ENV_VALUES
        for name in ("ALRAJHI_ENV", "FLASK_ENV", "ENV", "APP_ENV")
    )


def allow_legacy_unsigned_license() -> bool:
    """Legacy encrypted-only blobs remain accepted outside production.

    Production defaults to rejecting unsigned license blobs unless the operator
    deliberately sets ALRAJHI_ALLOW_LEGACY_UNSIGNED_LICENSE=1 for a controlled
    transition period.
    """
    override = os.environ.get("ALRAJHI_ALLOW_LEGACY_UNSIGNED_LICENSE")
    if override is not None:
        return str(override).strip().lower() in {"1", "true", "yes", "on"}
    return not is_production_environment()


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def key_fingerprint(license_key: str) -> str:
    """Store a stable fingerprint instead of the raw activation key."""
    return hashlib.sha256(str(license_key or "").encode("utf-8")).hexdigest()


def _parse_datetime(value: Any) -> Optional[_dt.datetime]:
    if not value:
        return None
    if isinstance(value, _dt.datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = _dt.datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = _dt.datetime.strptime(text[:10], "%Y-%m-%d")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.astimezone(_dt.timezone.utc)


def _expiration_from_payload(payload: Mapping[str, Any]) -> Any:
    return (
        payload.get("expiration")
        or payload.get("expirationDate")
        or payload.get("expires_at")
        or payload.get("valid_until")
    )


def is_expired(payload: Mapping[str, Any], *, now: Optional[_dt.datetime] = None) -> bool:
    expiration = _parse_datetime(_expiration_from_payload(payload))
    if expiration is None:
        return False
    current = now or _dt.datetime.now(_dt.timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=_dt.timezone.utc)
    return current.astimezone(_dt.timezone.utc) > expiration


def signed_payload_from_result(result: Mapping[str, Any]) -> Tuple[Optional[dict[str, Any]], Optional[str], Optional[str]]:
    """Normalize possible activation-server signed-license shapes."""
    payload = result.get("licensePayload") or result.get("payload") or result.get("license")
    signature = result.get("signature") or result.get("licenseSignature")
    algorithm = (result.get("algorithm") or result.get("signatureAlgorithm") or "ed25519").lower()
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = None
    if not isinstance(payload, dict) or not signature:
        return None, None, None
    return dict(payload), str(signature), algorithm


def verify_ed25519_signature(payload: Mapping[str, Any], signature: str, public_key_b64: str) -> bool:
    if Ed25519PublicKey is None:
        return False
    try:
        public_bytes = base64.b64decode(public_key_b64)
        signature_bytes = base64.b64decode(signature)
        key = Ed25519PublicKey.from_public_bytes(public_bytes)
        key.verify(signature_bytes, _canonical_json_bytes(payload))
        return True
    except (ValueError, TypeError, InvalidSignature):
        return False


def verify_signed_license_record(record: Mapping[str, Any]) -> bool:
    """Verify a signed license record if a public key is configured.

    The public key is intentionally externalized through ALRAJHI_LICENSE_PUBLIC_KEY
    so release builds can be signed without embedding a private or symmetric key.
    """
    payload = record.get("payload")
    signature = record.get("signature")
    algorithm = str(record.get("algorithm") or "").lower()
    public_key = os.environ.get("ALRAJHI_LICENSE_PUBLIC_KEY", "").strip()
    if not isinstance(payload, dict) or not signature or algorithm not in SIGNED_LICENSE_ALGORITHMS:
        return False
    if not public_key:
        return False
    return verify_ed25519_signature(payload, str(signature), public_key)


def build_license_record(
    *,
    license_key: str,
    device_id: str,
    server_result: Mapping[str, Any],
    feature_id: Optional[str] = None,
) -> dict[str, Any]:
    """Build the stored activation payload without persisting the raw key."""
    signed_payload, signature, algorithm = signed_payload_from_result(server_result)
    activated_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    if signed_payload is not None and signature is not None and algorithm is not None:
        record: dict[str, Any] = {
            "schema_version": LICENSE_SCHEMA_VERSION,
            "license_key_hash": key_fingerprint(license_key),
            "device": device_id,
            "feature": feature_id,
            "payload": signed_payload,
            "signature": signature,
            "algorithm": algorithm,
            "expiration": _expiration_from_payload(signed_payload) or server_result.get("expirationDate"),
            "activated_at": activated_at,
            "signed": True,
        }
    else:
        record = {
            "schema_version": LICENSE_SCHEMA_VERSION,
            "license_key_hash": key_fingerprint(license_key),
            "device": device_id,
            "feature": feature_id,
            "expiration": server_result.get("expirationDate"),
            "activated_at": activated_at,
            "signed": False,
            "legacy_unsigned": True,
        }
    if feature_id is None:
        record.pop("feature", None)
    return record


def _payload_claim(record: Mapping[str, Any], key: str) -> Any:
    payload = record.get("payload")
    if isinstance(payload, Mapping) and key in payload:
        return payload.get(key)
    return record.get(key)


def validate_license_record(
    record: Mapping[str, Any] | None,
    *,
    expected_device: str,
    expected_feature: Optional[str] = None,
    now: Optional[_dt.datetime] = None,
) -> Tuple[bool, str]:
    """Validate device binding, signature policy, feature claim and expiration."""
    if not isinstance(record, Mapping):
        return False, "ترخيص غير صالح"
    device = str(record.get("device") or _payload_claim(record, "device") or "")
    if not hmac.compare_digest(device, str(expected_device)):
        return False, "ترخيص غير صالح لهذا الجهاز"

    feature = _payload_claim(record, "feature")
    if expected_feature and feature and str(feature) != str(expected_feature):
        return False, f"ترخيص {expected_feature} غير صالح"

    signed = bool(record.get("signed"))
    if signed:
        if not verify_signed_license_record(record):
            return False, "توقيع الترخيص غير صالح أو مفتاح التحقق غير مضبوط"
    elif not allow_legacy_unsigned_license():
        return False, "ترخيص قديم غير موقّع مرفوض في وضع الإنتاج"

    if is_expired(record, now=now):
        return False, "انتهت صلاحية الترخيص"
    return True, ""


__all__ = [
    "LICENSE_SCHEMA_VERSION",
    "SIGNED_LICENSE_ALGORITHMS",
    "allow_legacy_unsigned_license",
    "build_license_record",
    "is_expired",
    "is_production_environment",
    "key_fingerprint",
    "signed_payload_from_result",
    "validate_license_record",
    "verify_signed_license_record",
]
