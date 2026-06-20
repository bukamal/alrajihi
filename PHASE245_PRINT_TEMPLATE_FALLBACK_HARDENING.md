# PHASE245 — Print Template Fallback Hardening

## Scope
Harden browser HTML printing so missing or broken real templates no longer produce weak business documents silently.

## Contract
- Real templates remain loaded through `printing._template_loader.require_template`.
- Missing templates now render a visible localized browser HTML diagnostic page by default.
- The emergency simplified renderer is available only when `printing/allow_emergency_fallback=true` or `ALRAJHI_PRINT_ALLOW_EMERGENCY_FALLBACK=1`.
- Diagnostics are controlled through `printing/show_template_diagnostics`.
- Both settings are read through `SettingsService` and therefore through the existing SettingsGateway/API boundary in client/server deployments.
- Arabic, German, and English labels are supported.

## Files
- `alrajhi_client/printing/_template_loader.py`
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/features/settings/settings_document_tabs.py`
- `alrajhi_client/i18n/translator.py`
- `tests/test_phase245_print_template_fallback_hardening.py`
