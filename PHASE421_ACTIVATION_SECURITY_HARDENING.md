# Phase 421 — Activation & Security Hardening

## Purpose

Phase 421 hardens the activation and server diagnostic surfaces before any wider distribution or multi-user deployment.  The phase does not remove the existing activation flow.  It inserts a stricter validation boundary that supports signed license payloads, local expiration checks, feature-claim validation, and production-only rejection of unsigned legacy activation blobs.

## Client activation changes

Added:

- `alrajhi_client/auth/license_security.py`
- `alrajhi_client/workspace/quality/activation_security_contract.py`
- `alrajhi_client/workspace/quality/activation_security_audit.py`

`activation.py` now builds stored records through `build_license_record()` and validates them through `validate_license_record()`.

New activation records store:

- `schema_version`
- `license_key_hash`
- `device`
- optional `feature`
- `expiration`
- `activated_at`
- optional signed `payload/signature/algorithm`

New records no longer persist the raw license key.  Old encrypted-only blobs can still be read outside production to avoid breaking existing local installs.

## Signed license policy

The new contract supports Ed25519 signed license payloads.  Verification uses an external public key from:

`ALRAJHI_LICENSE_PUBLIC_KEY`

No private or symmetric signing secret is embedded in the client.  In production/release environments, unsigned legacy activation blobs are rejected by default unless an operator deliberately sets:

`ALRAJHI_ALLOW_LEGACY_UNSIGNED_LICENSE=1`

This override exists only as a migration escape hatch.

## Expiration and feature claims

`check_activation()` and `check_feature_activation()` now validate:

- device binding
- signature policy
- expiration date
- requested feature id when checking module activation

Device comparison uses constant-time comparison to avoid leaking matching progress.

## Server diagnostic hardening

Added:

- `alrajhi_server/services/security_runtime.py`

`/api/routes` is now hidden unless diagnostics are enabled.  Production/release environments disable diagnostics by default.  The operator must set:

`ALRAJHI_ENABLE_DIAGNOSTICS=1`

The following diagnostic routes are also guarded by diagnostic mode and JWT:

- `/api/debug/status`
- `/api/monitoring/health`

JWT secret enforcement from previous phases remains intact: `ALRAJHI_JWT_SECRET` is required in production.

## Added guards and tests

Added:

- `tools/phase421_activation_security_guard.py`
- `tests/test_phase421_activation_security.py`

The guard writes:

- `tools/audit_outputs/activation_security_matrix.csv`

## Verification target

The phase should pass:

```bash
python tools/phase421_activation_security_guard.py
pytest -q tests/test_phase421_activation_security.py
python -m compileall alrajhi_client alrajhi_server tools tests
```

## Remaining security backlog

Phase 421 does not implement full online revocation.  That belongs in a later phase once the license server protocol is finalized.  It also does not create database-level idempotency uniqueness; that remains tracked by the Phase 420 backlog.
