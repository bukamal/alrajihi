# Phase 274 — Settings Grouped Navigation

## Goal

Reduce the crowded top-level Settings tabs without deleting any settings page or changing the underlying settings keys, API paths, save handlers, language behavior, or diagnostics.

## What changed

The existing Phase 273 leaf registry remains the canonical source of all settings pages:

- company
- appearance
- languages
- profiles
- invoices
- returns
- currency
- rates
- workflow
- reports
- units
- inventory
- manufacturing
- printing
- POS
- network
- security
- security events
- settings audit
- backup
- contracts
- diagnostics

A new grouped navigation layer presents these pages under six top-level groups:

1. General
2. Finance & Reports
3. Inventory & Manufacturing
4. Operations, Print & Network
5. Security, Backup & Audit
6. Diagnostics & Contracts

Each top-level group contains a nested tab widget for the existing pages.

## Compatibility

- Existing settings functions are not renamed.
- Existing save handlers are not changed.
- Existing settings keys are not migrated.
- Existing API/network behavior is untouched.
- The diagnostics tab remains inside Settings; it is grouped under Diagnostics & Contracts.
- Language refresh updates both top-level group labels and nested leaf tab labels from the same registries.

## Verification

Added `tests/test_phase274_settings_grouped_navigation.py`.

The test verifies:

- grouped navigation is used;
- every old leaf tab is present exactly once;
- no tab title/content drift can reappear;
- Arabic, English, and German translations exist for all top-level groups.
