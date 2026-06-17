# Phase 156 - Receivables / Payables & Aging

Implemented in code:

- Accounting receivables aging based on unpaid sale invoices.
- Accounting payables aging based on unpaid purchase invoices.
- Customer accounting statement from invoices and vouchers.
- Supplier accounting statement from invoices and vouchers.
- REST endpoints:
  - GET /api/reports/accounting/receivables/aging
  - GET /api/reports/accounting/payables/aging
  - GET /api/reports/accounting/customers/<id>/statement
  - GET /api/reports/accounting/suppliers/<id>/statement
- Remote client methods for all endpoints.
- Safe due_date column support for invoices.

Validation performed:

- Python compileall.
- Runtime local accounting AR/AP scenario: unpaid sales invoice, unpaid purchase invoice, customer receipt voucher, supplier payment voucher.

Scope note:

This phase implements operational AR/AP reporting. It does not yet implement automated allocation of partial payments to individual invoice installments.
