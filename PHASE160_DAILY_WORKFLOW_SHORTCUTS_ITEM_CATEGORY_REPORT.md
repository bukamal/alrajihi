# Phase 160 - Daily Workflow, Shortcuts, and Item Category Hotfix

## Scope
Implemented the requested daily-use behavior on top of the optional workflow build.

## Implemented

### 1. Automatic posting when Workflow is disabled
When `workflow/enabled = false`, newly saved sale/purchase invoices are automatically posted.

Client-side behavior:
- `InvoiceService.create(...)` now calls `post(...)` after invoice creation when Workflow is disabled.
- Auto-post failures are logged with `AUTO_POST_FAILED` without crashing the invoice save flow.

Server/API behavior:
- `POST /api/invoices` also posts the invoice immediately when Workflow is disabled.
- The invoice gets `workflow_status = POSTED` and a `workflow_events` entry with action `auto_post`.

### 2. Daily shortcuts open dialogs only
Dashboard daily shortcuts no longer navigate to management pages before opening forms.

Affected shortcuts:
- Sale invoice
- Purchase invoice
- New item
- New customer
- New supplier
- Receipt voucher
- Payment voucher

Main quick menu was aligned with the same behavior.

### 3. Add category from New Item dialog
The item dialog now includes a `+` button next to the category selector.

Behavior:
- User can create a category from inside the item dialog.
- Category list refreshes immediately.
- Newly created category is selected automatically.

## Validation
- `python -m compileall -q alrajhi_client alrajhi_server tools`: PASSED
- `python tools/architecture_guard.py`: PASSED
- Static verification: dashboard daily shortcut handlers do not call `switch_page(...)`: PASSED
- Static verification: client and server include auto-post path when Workflow is disabled: PASSED

## Notes
GUI click automation was not executed in this environment. The changes were implemented structurally and validated by compile/architecture/static checks.
