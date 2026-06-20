# Phase 255 — Party/Voucher/Dashboard Shell Cleanup

This phase closes the remaining shell compatibility gaps without reversing the
Document Shell direction introduced in phases 249–254.

## Scope

- Customer and supplier list screens keep `main.open_party_document(...)` as the
  official route. `AddEntityDialog` is retained only as an emergency fallback
  when a list widget is embedded outside `MainWindow`/`TabbedWorkspace`.
- `PartyEditorTab` now uses canonical document types (`customer` / `supplier`)
  so `DocumentDescriptor` and `DocumentPermissionBinder` apply correctly.
- `VoucherEditorTab` hosts the existing `VoucherActionsPanel` inside the unified
  bottom action bar. Print/export still go through `PrintingService`; the
  `voucher_preview` and `voucher_pdf` methods are browser-backed compatibility
  methods after Phase 242.
- The dashboard restores `ModernKpiCard` and `DashboardChartPanel` as visual-only
  components fed by `DashboardService.snapshot()`. No printing/database access is
  introduced in dashboard UI code.

## Network/API/language/security posture

The phase does not add local-only persistence. Parties and vouchers remain behind
services/gateways and their existing API resources. Button enablement continues
through Document Shell descriptors and permission binder. All visible text uses
i18n translation helpers. Monetary values continue to use the unified currency
formatting policy.
