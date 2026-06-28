# -*- coding: utf-8 -*-
"""Phase 421 activation and security hardening contract."""
from __future__ import annotations

ACTIVATION_SECURITY_CONTRACT = {
    "phase": 421,
    "name": "Activation & Security Hardening",
    "license_invariants": (
        "new_license_records_store_license_key_hash_not_raw_key",
        "license_records_validate_device_binding_with_constant_time_compare",
        "expiration_is_checked_locally",
        "signed_license_payloads_are_supported_through_external_public_key",
        "unsigned_legacy_licenses_are_rejected_by_default_in_production",
        "feature_license_claims_are_checked_against_requested_feature",
    ),
    "server_invariants": (
        "jwt_secret_required_in_production",
        "api_routes_endpoint_hidden_when_diagnostics_disabled",
        "debug_status_route_requires_diagnostic_mode_and_jwt",
        "monitoring_health_route_requires_diagnostic_mode_and_jwt",
        "diagnostic_mode_is_explicitly_enabled_by_environment_flag",
    ),
    "accepted_transition_risks": (
        "legacy encrypted-only license blobs remain accepted outside production for migration",
        "full online revocation check is still a follow-up phase",
        "persistent server-side idempotency uniqueness remains covered by Phase420 backlog",
    ),
}


def contract_summary() -> dict[str, object]:
    return {
        "phase": ACTIVATION_SECURITY_CONTRACT["phase"],
        "name": ACTIVATION_SECURITY_CONTRACT["name"],
        "license_invariant_count": len(ACTIVATION_SECURITY_CONTRACT["license_invariants"]),
        "server_invariant_count": len(ACTIVATION_SECURITY_CONTRACT["server_invariants"]),
        "accepted_transition_risks": tuple(ACTIVATION_SECURITY_CONTRACT["accepted_transition_risks"]),
    }


__all__ = ["ACTIVATION_SECURITY_CONTRACT", "contract_summary"]
