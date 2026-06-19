# Phase 232 — Dashboard Cashbox / Language Audit

## Objective
Fix the dashboard cashbox card so it reads from the modern cashbox subsystem and add a repeatable language audit for visible UI text.

## Fixes
- `DashboardService.snapshot()` now includes `cash_bank_summary`.
- `DashboardService.summary()` prefers `reporting_service.cash_bank_summary().cash_total` over the legacy `users.cash_balance` when cashboxes exist.
- `DashboardService.cashbox_movement()` reads `reporting_service.cash_bank_movements()` and summarizes real ledger rows for today and general movement.
- `DashboardWidget` reads `cash_bank_summary` and displays `cash_total` in the cashbox card.
- Dashboard cashbox amounts now use `currency.format_base_amount(...)` instead of hard-coded `USD` conversion.
- Dashboard exchange-rate text no longer hard-codes `1 USD`; it uses the configured storage/base currency.
- Removed duplicated dashboard cash amount methods left by previous UI edits.
- Added dashboard status translation keys for Arabic, German, and English.

## Audits / Guards
- `tools/phase232_dashboard_cashbox_language_guard.py`
- `tools/phase232_project_language_audit.py`
- `tools/audit_outputs/phase232_dashboard_cashbox_language_audit.json`
- `tools/audit_outputs/PHASE232_DASHBOARD_CASHBOX_LANGUAGE_AUDIT.md`
- `tools/audit_outputs/phase232_project_language_audit.json`
- `tools/audit_outputs/PHASE232_PROJECT_LANGUAGE_AUDIT.md`

## Analysis result
The dashboard cashbox problem was caused by the dashboard using the legacy `users.cash_balance` field while the migrated finance subsystem stores the authoritative cashbox state in `cashboxes` and `cash_bank_movements`.

The language audit found remaining likely visible literals in several old or broad screens, mostly settings and legacy dialogs. This does not block runtime, but it should be reduced in future cleanup phases.
