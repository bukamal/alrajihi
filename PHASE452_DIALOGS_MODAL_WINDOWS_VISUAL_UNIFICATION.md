# Phase 452 — Dialogs & Modal Windows Visual Unification

This phase centralizes the visual identity for dialogs and modal windows.

Scope:

- Generic `QDialog` instances.
- `QMessageBox` prompts that remain modal, including questions and confirmations.
- Frameless/centered dialogs.
- Modern dialogs using `apply_modern_dialog`.
- Network settings fallback dialog.
- Change password dialog.
- Module activation dialog.
- Barcode camera dialog.
- Tables, tabs, inputs, headers, body surfaces, footers and action buttons inside modals.

Non-goals:

- No changes to accept/reject behavior.
- No changes to activation logic.
- No changes to password validation.
- No changes to camera/barcode scanning.
- No changes to message/toast replacement behavior.
- No changes to persistence, service calls, printing or routing.

Implementation:

- Added Phase452 modal tokens to `theme/brand.py`.
- Added central QSS selectors in `theme/qss.py` keyed by `modalVisualPhase="452"` and `visualRole="modal_*"`.
- Extended `ui/dialog_branding.py` with `apply_modal_visual_template`.
- Added `ui/modal_visual_event_filter.py` so dialogs created outside branded helpers still receive Phase452 roles when shown.
- Installed the filter after `ThemeManager.init_app(app)`.
- Suppressed legacy local frameless dialog styling that could override the global QSS.
- Migrated selected high-impact dialogs to semantic modal roles.
