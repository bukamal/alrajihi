# GATEWAY PHASE 64 - Dashboard Branding, Navigation Labels, Login Title Hotfix

## Scope
Applied requested UI branding refinements:

1. Dashboard: replaced the old runtime status card with the project logo card.
2. Dashboard company card: kept company logo source as settings-driven with project logo fallback.
3. Top utility icons: added visible labels under icon buttons.
4. Main navigation menu: adjusted menu labels to display below icons where supported by Qt menu rendering.
5. Login screen: changed visible product title to "الراجحي للمحاسبة".

## Modified files

- `alrajhi_client/views/widgets/dashboard_widget.py`
- `alrajhi_client/views/modern_topbar.py`
- `alrajhi_client/views/main_window.py`
- `alrajhi_client/views/dialogs/login_dialog.py`

## Details

### Dashboard
- Replaced `_create_health_panel()` placement with `_create_brand_panel()`.
- The new card shows:
  - Project logo from `logo_png(512)`.
  - Text: `الراجحي للمحاسبة والمستودعات والتصنيع`.
  - Subtitle: `نظام إدارة متكامل`.
- `_refresh_health()` is now no-op when the health card is not displayed.

### Company information card
- Existing behavior retained:
  - Reads `company/logo_path` from settings via `get_company_info()`.
  - Falls back to `logo_png(256/512)` when the configured logo path is empty or invalid.

### Navigation and title/utility bar
- Alert and theme buttons now show text under icons:
  - `التنبيهات`
  - `الثيم`
- Main ERP QMenuBar menu titles were changed to newline-prefixed labels so the label appears below the icon where Qt/platform rendering supports it.
- Menu bar height and item padding were increased to fit icon + text.

### Login screen
- Login hero title changed from the global app display name to:
  - `الراجحي للمحاسبة`
- Login subtitle changed to:
  - `نظام الراجحي للمحاسبة — تسجيل دخول آمن`

## Validation
Compiled successfully with:

```bash
python3 -m py_compile \
  alrajhi_client/views/widgets/dashboard_widget.py \
  alrajhi_client/views/modern_topbar.py \
  alrajhi_client/views/main_window.py \
  alrajhi_client/views/dialogs/login_dialog.py
```
