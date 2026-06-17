# GATEWAY PHASE 77 – LANGUAGE UI MIGRATION CORE REPORT

## Scope
Phase 77 continues the language refactor after Phase 76 foundation. It migrates core user-facing shell text to the centralized language system while keeping the change set safe and limited.

## Languages
- Arabic: primary/default, RTL.
- German: second language, LTR.
- English: third language, LTR.
- French remains unsupported and is normalized to Arabic for backward compatibility only.

## Implemented
- Expanded the central translation dictionary in `alrajhi_client/i18n/translator.py`.
- Migrated the main navigation menus in `views/main_window.py` to translation keys.
- Migrated page titles/breadcrumb composition to dynamic translated values.
- Migrated shell utility bar labels/placeholders in `views/modern_topbar.py`.
- Improved login dialog live language switching so title, subtitle, mode, buttons and warnings update.
- Migrated the Settings header, appearance tab and settings tab captions to translation keys.
- Language changes from Settings now refresh the main menu and topbar text without restarting.

## Safety notes
- No database schema changes.
- No runtime event filters.
- No QtWebEngine/Chromium flags.
- No broad replacement of all Arabic literals yet; this phase targets the core shell.

## Verification
- `python3 tools/verify_language_migration_phase77.py` passed.
- `python3 -m compileall -q alrajhi_client` passed.

## Next recommended phase
Phase 78 should migrate transaction modules one group at a time: sales invoices, purchase invoices, returns, vouchers, and POS. This avoids a high-risk global text replacement.
