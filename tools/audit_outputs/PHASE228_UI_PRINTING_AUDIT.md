# Phase 228 UI / Printing Audit

## Summary
- high: 0
- medium: 0
- low: 24

## Opinion
- Dashboard simplification is correct: the removed KPI/chart layer was visually heavy and duplicated deeper reports.
- The global top search should stay removed; page-local search is clearer and less surprising in an ERP shell.
- Printing is now mostly centralized around HTML via printing_service, but the remaining thermal/barcode internals should stay isolated in the printing package only.
- The next UX cleanup should standardize document-shell action placement: one top-level workspace action bar plus one local document bottom bar, not scattered print/save buttons.

## Findings
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/dialogs/batch_print_dialog.py:48)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/dialogs/invoice_dialog.py:692)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/dialogs/production_details_dialog.py:88)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/dialogs/production_details_dialog.py:88)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/reports_widget.py:98)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/returns_widget.py:326)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/returns_widget.py:326)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/vouchers_widget.py:52)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/warehouses_widget.py:117)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/warehouses_widget.py:117)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/warehouses_widget.py:190)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/warehouses_widget.py:190)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/components/table_toolbar.py:75)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/views/widgets/components/table_toolbar.py:75)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/manufacturing/bom_document_tab.py:160)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/manufacturing/bom_document_tab.py:160)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:136)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:136)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/parties/party_editor_tab.py:227)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/vouchers/voucher_editor_tab.py:179)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/finance/documents/expense_document_tab.py:231)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py:92)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py:92)
- [low] button-duplication — Potential local print button; prefer workspace/action-shell or document shell print menu. (alrajhi_client/features/vouchers/components/voucher_actions.py:22)
