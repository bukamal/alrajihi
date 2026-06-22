# Phase 332 — Design Tokens and Typography Normalization

This phase starts the project-wide visual unification track on top of the Phase 331 UI registry.
It does not replace feature layouts yet.  It establishes a single typography and shell-size contract so future workspace, action-bar, table, column, printing and barcode phases do not add new local font/size constants.

## Scope

- Added central typography and shell metrics to `theme/brand.py`.
- Exposed the same values through `ui/design_system.py` for dialogs and feature widgets.
- Updated global QSS to consume body, caption, value, menu, action button, input and table padding tokens.
- Upgraded the primary icon menu from the previous tiny 60px/9px style to tokenized 74px navigation with larger icons, font size and menu rows.
- Upgraded `UnifiedActionBar` to tokenized height, icon size, button height and font size.
- Kept Phase 331 page registry and module visibility policies intact.

## Non-goals

- This phase does not yet rebuild every feature widget.
- This phase does not yet apply the universal column contract.
- This phase does not yet implement barcode multi-print profiles.

Those follow in later phases after the shell typography baseline is stable.
