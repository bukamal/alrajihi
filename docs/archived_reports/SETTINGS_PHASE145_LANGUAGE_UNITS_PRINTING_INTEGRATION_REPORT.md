# Phase 145 — Language, Units & Printing Runtime Integration

## Scope
This phase continues the professional Settings module by turning saved language/unit/company settings into runtime controls used by printing and system behavior.

## Implemented

### 1. Independent language settings
- Added a dedicated **Languages** settings tab.
- Added separate controls for:
  - UI language
  - Print/PDF language
  - Reports language
- Updated appearance save logic so changing UI language no longer overwrites print/report language.

### 2. SettingsService language helpers
Added runtime helpers:
- `print_language()`
- `report_language()`
- `save_language_settings(ui_language, print_language, report_language)`

### 3. Unit settings integration
- Fixed canonical unit key mismatch:
  - old key: `units/default_sale_unit`
  - canonical key: `units/default_sales_unit`
- Kept backward compatibility by reading/writing both where needed.
- Added runtime helpers:
  - `quantity_decimals()`
  - `price_decimals()`
  - `format_quantity(value)`
  - `format_price(value)`
  - `save_units_settings(...)`

### 4. Company settings as runtime source
- Added `SettingsService.save_company_info(info)`.
- Company changes are now persisted both to legacy config and SettingsService keys.
- Printing can now read company identity from SettingsService instead of relying only on legacy config.

### 5. Printing integration
- `print_templates.py` now uses `settings_service.print_language()` for document direction/language decisions.
- Company header now reads from `settings_service.company_info()`.
- Added commercial register and website to printable company header when available.

## Validation
- Full Python compile check passed:
  - `python -m compileall -q alrajhi_client`

## Files touched
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/printing/print_templates.py`

## Notes
This phase is deliberately backward-compatible. Existing screens that still read old keys continue to work while new code uses canonical settings helpers.
