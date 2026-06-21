# Phase 284 — Restaurant Table Map Filters

## Scope

This phase continues the restaurant operation-shell UX work from Phase 283. It improves the table map itself instead of adding more crowded operational panels.

## Changes

- Added a table search box to the restaurant table map.
- Added status filtering: all, free, occupied, waiting kitchen, ready, payment, reserved.
- Added zone/floor/area filtering using `zone`, `area`, `floor`, or `section` fields from table records.
- Added live table counters above the map for every operational state.
- Kept the existing table-click workflow unchanged.
- Added empty-state messaging when filters produce no results.
- Added Arabic, English, and German translations.
- Added QSS styling for the new filter bar, counter bar, search input, status selector, zone selector, and empty state.

## Intent

The restaurant screen should now support fast floor-service operation: filter by room/zone, locate a table quickly, and see the operational load at a glance.
