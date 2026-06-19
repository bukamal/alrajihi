# Phase 214 — Reports Governance / Export Hardening

This phase introduces a central report operation policy and binds report viewing
and report export/printing to settings, RBAC permissions and audit logging.

Key changes:

- Added `core/services/report_operation_policy.py` with `OP_VIEW` and `OP_EXPORT`.
- Added `settings_service.get_report_settings()`.
- ReportsWidget now disables report controls when reports are not allowed.
- Report printing/export now requires `reports.export` through the policy.
- Added i18n keys for report operation labels and denial messages.
- Added `tools/phase214_reports_governance_guard.py`.

The report rendering logic remains in the existing widget/mixins. This phase is
conservative and focuses on governance, not rewriting report calculations.
