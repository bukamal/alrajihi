# Phase 446 — Shell Header & Action Bar Visual Consolidation

## Scope

This phase consolidates the visual identity of the global shell chrome: the main navigation bar and the global action bar.  These surfaces are visible on almost every screen, so they must stop competing visually with workspace content.

## What changed

- Main navigation now uses calm project identity surfaces rather than strong legacy Basit blue buttons everywhere.
- Home remains an accent surface, but normal menu groups are quieter cards with hover/active indicators.
- UnifiedActionBar is now secondary chrome: it supports the active workspace without visually overpowering it.
- Shell controls are tagged with semantic visual roles:
  - `shell_navigation`
  - `shell_nav_button`
  - `shell_action_bar`
  - `shell_action_button`
  - `shell_action_utility`
  - `shell_action_user`
- The central brand tokens now include Phase446 shell colors, borders, hover states, and compact widths.

## Non-goals

No navigation routing, permissions, page loading, printing, POS logic, restaurant logic, table behavior, or accounting logic was changed.

## Verification

- `tools/phase446_shell_header_action_bar_visual_guard.py`
- `tests/test_phase446_shell_header_action_bar_visual_consolidation.py`

