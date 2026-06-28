# Phase 414 — Legacy Elimination Foundation

This phase stops patching over legacy UI paths and creates a hard boundary for the next cleanup round.

## Implemented

- Replaced the shell navigation surface with `CleanShellNavigationBar`.
- Removed the hidden top-bar widget from the main shell layout.
- Kept only a non-visual compatibility adapter for optional button checks.
- Removed QToolButton-based main-navigation popup behavior from `MainWindow`.
- Main navigation now uses `QPushButton` plus manual `QMenu.popup()` only.
- Disabled legacy invoice and return fallbacks in `MainWindow`.
- Made `allow_legacy_transaction_documents()` return `False` unconditionally.
- Removed legacy invoice/return editor exports from package-level imports.
- Added a guard to ensure the old routes cannot re-enter the production shell.

## Why

The unresolved upper-left shell overlap and editable-grid Enter conflicts show that old compatibility layers were still active below newer fixes.  This phase starts the cleanup by removing the old shell surface from runtime and blocking old transaction-document routing.

## Next

Phase 415 should migrate the sales invoice line editor fully onto one unified grid model/navigation lifecycle and add runtime key-navigation tests.  No legacy `InvoiceDialog` or `LinesModel` path should be used for production routing.
