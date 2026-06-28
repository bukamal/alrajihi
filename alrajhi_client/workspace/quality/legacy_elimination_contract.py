# -*- coding: utf-8 -*-
"""Phase414 legacy elimination foundation contract."""
from __future__ import annotations

LEGACY_ELIMINATION_CONTRACT = {
    "phase": 414,
    "name": "legacy_elimination_foundation",
    "scope": [
        "views.main_window shell navigation",
        "transaction document routing",
        "legacy invoice/return adapter exports",
    ],
    "requirements": [
        "MainWindow must instantiate CleanShellNavigationBar, not the old icon menu shell.",
        "No hidden utility top-bar QWidget may be added to the main shell layout.",
        "Shell navigation must use QPushButton with manual QMenu.popup(), not native QToolButton menu subcontrols.",
        "Invoice and return creation/edit routes must use unified TransactionDocumentTab surfaces only.",
        "Legacy invoice/return package exports must be disabled so old adapters cannot be imported by new routes.",
        "allow_legacy_transaction_documents must return False unconditionally.",
    ],
    "required_outputs": [
        "tools/audit_outputs/legacy_elimination_foundation_matrix.csv",
    ],
}

LEGACY_BANNED_MAIN_WINDOW_PATTERNS = (
    "from views.modern_topbar import",
    "ModernTopBar(",
    "class IconMenuBar",
    "self.menu_bar = IconMenuBar",
    "QToolButton#MainNavToolButton",
    "btn.setMenu(menu)",
    "QToolButton.InstantPopup",
    "main_layout.addWidget(self.top_bar)",
    "from features.invoices import InvoiceEditorTab",
    "from features.returns import SalesReturnEditorTab",
    "from features.returns import PurchaseReturnEditorTab",
    "ReturnEditorTab =",
)

LEGACY_ALLOWED_ISOLATED_FILES = {
    "alrajhi_client/features/invoices/invoice_editor_tab.py",
    "alrajhi_client/features/returns/return_editor_tabs.py",
}
