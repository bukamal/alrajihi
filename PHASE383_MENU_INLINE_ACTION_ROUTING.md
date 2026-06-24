# Phase 383 — Menu Inline Action Routing

This phase makes creation commands from the main menu and shared action bar obey
the inline workspace contract.

## Scope

- The action-bar **New** command is context-aware.
- Management workspaces create records inside their own inline editor surface:
  customers, suppliers, categories, vouchers, warehouses, branches, cashboxes,
  and users.
- The Finance menu exposes receipt, payment, and expense voucher creation and
  keeps each path inside the Vouchers workspace.
- Warehouse, branch, cashbox, bank-account, and user creation entries are routed
  through their owning workspaces instead of standalone document tabs.
- Document-list workspaces still open their proper document family rather than
  defaulting everything to sales invoices.

## Guard

`tools/phase383_menu_inline_action_routing_guard.py`
