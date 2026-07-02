# Phase 454 — Runtime Layout Reconstruction

Phase 454 responds to the Windows runtime screenshots after Phase 453.  It is a layout/density correction pass, not a business-logic pass.

## Scope

- Login runtime split layout and compact chrome.
- Shell action-bar density reduction.
- POS barcode-first runtime structure: top tools, context bar, scan bar, major table, payment footer.
- Invoice editor runtime structure: header fields, quick-entry card, major grid, financial summary, sticky footer.
- Material editor runtime structure: rebalanced cards and stronger action footer.
- Arabic cleanup for shortcut fragments that remained English in runtime labels.

## Non-goals

No change to persistence, DAO/API, Enter navigation, stock calculations, invoice totals, printing, permissions, routing, or activation.
