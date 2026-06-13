# Phase 49 - Offline Invoice Refresh Hotfix

## Problem
When a client creates/saves a purchase invoice while the server is down, the invoice save path may be queued successfully, but the invoices widget immediately calls `refresh_all()` and then performs a non-queueable read:

- `GET /api/invoices?type=purchase...`
- sometimes also reads customers/suppliers while offline.

Because these are read operations and cannot be queued safely, the REST client raises:

`No connection and this operation cannot be queued safely: /api/invoices`

The unhandled exception in the PyQt slot aborts the application.

## Fix
Updated `alrajhi_client/views/widgets/invoices_widget.py`:

- Added `_is_offline_read_error()` helper.
- Added `_notify_offline_read()` warning toast.
- Wrapped customer/supplier preload reads with offline-safe handling.
- Wrapped invoice list refresh for sale/purchase with offline-safe handling.
- Wrapped `refresh_all()` to prevent UI crash when the server is offline.

## Behavior After Fix
- Saving an invoice while server is down no longer aborts the client.
- The write operation can still enter Offline Queue.
- The table refresh is skipped with a warning until the server returns.
- Once the server is available, normal refresh/sync resumes.

## Server Update?
This specific crash is client-side. Updating the server will not fix the crash if the server is intentionally stopped. However, production deployment should keep client and server on the same release to avoid API mismatches.

## Validation
- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
- offline_read_guard: PASS
- zip test: PASS
