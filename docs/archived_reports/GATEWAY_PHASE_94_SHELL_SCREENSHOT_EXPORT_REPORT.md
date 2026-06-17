# GATEWAY PHASE 94 — Shell Screenshot Export & Icon-only Utility Buttons

## Scope
- Removed visible labels from the theme button and notification button in all languages.
- Kept tooltips translated for accessibility.
- Added a screenshot export button beside the notification/theme buttons.
- Added an in-app export dialog using `QFileDialog.getSaveFileName`.
- Supports PNG and JPEG export.

## Modified files
- `alrajhi_client/views/modern_topbar.py`
- `alrajhi_client/views/main_window.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/i18n/translator.py`

## Validation
- `compileall`: passed.
- No visible translated text remains on alert/theme utility buttons.
- Screenshot button uses icon-only display and translated tooltip.
