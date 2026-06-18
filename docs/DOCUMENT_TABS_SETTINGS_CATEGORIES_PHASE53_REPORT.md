# Phase 53 — Settings/Categories Document Tabs

## Scope
- Decomposed `CategoryEditorTab` into header and properties panels.
- Added settings section document tabs for company, accounting, inventory, restaurant, printing, UI, and security settings.
- Integrated settings sections into workspace quick-open using `settings:<section>` entries.

## Boundary rules
- Settings tabs persist only through `settings_service`.
- Category tabs persist only through `product_service`.
- No direct database access was added to UI/features.

## Follow-up
The legacy `settings_widget.py` remains as the settings hub for compatibility. Future phases should progressively route its buttons to the new settings section tabs and reduce the monolithic file.
