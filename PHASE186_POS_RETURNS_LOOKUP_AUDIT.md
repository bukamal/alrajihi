# Phase 186 — POS / Returns Lookup Audit

This phase audits material-name lookup behavior outside normal invoice grids.

## Findings

- Normal POS has no editable material-name cell. It adds lines through `POSService.add_scan()` and the unified `barcode_input_service.lookup_entry()` path. Manual text lookup is already case-insensitive through the item API/search fixes from Phase 184.
- Restaurant POS menu-card search still used plain SQLite `LIKE`, which could become case-sensitive under `PRAGMA case_sensitive_like=ON` or vary in remote SQL contexts. It is now explicitly `LOWER(...) LIKE LOWER(?)` on local and server repositories.
- Sales/purchase returns do not let the user type a material name into the line grid. Return material cells are loaded from the original invoice and are read-only; only quantity/unit/reason are editable.
- Shared `TransactionLineGrid` now installs item/unit delegates only for editable schema columns. This prevents read-only POS, restaurant, and returns grids from accidentally opening material/unit editors.

## Guard

`tools/phase186_pos_returns_lookup_audit_guard.py` verifies the behavior above.
