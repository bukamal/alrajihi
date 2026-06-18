# Phase 192 — Manufacturing Printing Bridge

Implemented unified manufacturing printing through `ManufacturingPrintingBridge`.

Outputs added:

- BOM / manufacturing recipe
- Production order
- Raw-material pick ticket
- Production cost report

Rules:

- UI tabs do not build printable HTML directly.
- All manufacturing printing goes through `manufacturing_operation_policy.OP_PRINT`.
- Printable HTML is owned by `printing.print_templates`.
- Preview/print/PDF are exposed by `printing_service`.
- Paper/template selection is settings-driven.
