# -*- coding: utf-8 -*-
"""Phase450 Unified Document Editor Visual Template contract.

Qt-free/static guard: document editors must receive a central visual template
through document_layout_policy instead of feature-local QSS blocks.  The phase
keeps business logic untouched while unifying headers, cards, tables, summary
panels, inputs and bottom action bars for invoices, returns, vouchers,
transfers, manufacturing and master-data document editors.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "document_editor_visual_phase",
    "document_editor_surface_bg",
    "document_editor_header_bg",
    "document_editor_card_bg",
    "document_editor_summary_bg",
    "document_editor_action_bar_bg",
    "document_editor_input_bg",
    "document_editor_table_header_bg",
    "document_editor_primary_bg",
    "document_editor_secondary_bg",
    "document_editor_danger_bg",
]

REQUIRED_QSS_MARKERS = [
    "Phase450: unified document editor visual template",
    'QWidget[documentVisualTemplatePhase="450"]',
    'visualRole="document_editor_surface"',
    'visualRole="document_header"',
    'visualRole="document_card"',
    'visualRole="document_summary"',
    'visualRole="document_action_bar"',
    'visualRole="document_input"',
    'visualRole="document_table"',
    'visualRole="document_primary_action"',
    'visualRole="document_danger_action"',
]

REQUIRED_POLICY_MARKERS = [
    "def _apply_document_visual_template",
    'widget.setProperty("documentVisualTemplatePhase", 450)',
    'widget.setProperty("visualWorkspaceType", "document")',
    '"document_header"',
    '"document_card"',
    '"document_summary"',
    '"document_action_bar"',
    '"document_table"',
    '"document_primary_action"',
    '_apply_document_visual_template(widget, kind=resolved_kind)',
]

STYLE_SUPPRESSION_TARGETS = [
    "alrajhi_client/features/categories/category_editor_tab.py",
    "alrajhi_client/features/finance/documents/expense_document_tab.py",
    "alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py",
    "alrajhi_client/features/manufacturing/bom_document_tab.py",
    "alrajhi_client/features/manufacturing/production_order_document_tab.py",
    "alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py",
    "alrajhi_client/features/parties/party_editor_tab.py",
    "alrajhi_client/features/settings/settings_document_tabs.py",
    "alrajhi_client/features/vouchers/voucher_editor_tab.py",
]

FORBIDDEN_DOCUMENT_LOCAL_STYLE_SNIPPETS = [
    "QFrame#DocumentHeaderCard, QFrame#FormCard",
    "QFrame#DocumentHeaderCard, QFrame#DocumentPanel, QFrame#SummaryPanel",
    "QFrame#ExpenseDocumentHeaderCard, QFrame#ExpenseDocumentPanel",
    "QFrame#DocumentHeaderCard, QFrame#FormCard, QFrame#BomSummaryPanel",
    "QFrame#BottomActionBar { background: palette(window); }",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase450_unified_document_editor_visual_template_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase450 document brand token: {token}")
    checks += 1
    if "'document_editor_visual_phase': 450" not in brand:
        details.append("document_editor_visual_phase must be 450")
    checks += 1
    if not any(marker in brand for marker in ("'project_visual_identity_phase': 450", "'project_visual_identity_phase': 451")):
        details.append("project_visual_identity_phase must advance to 450 or later")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing document marker: {marker}")
    checks += 1
    if qss.find("Phase450: unified document editor visual template") < qss.find("Phase449: reports workspace visual refactor"):
        details.append("Phase450 document QSS must come after Phase449 report rules")

    policy = _read(root, "alrajhi_client/workspace/documents/document_layout_policy.py")
    for marker in REQUIRED_POLICY_MARKERS:
        checks += 1
        if marker not in policy:
            details.append(f"document layout policy missing marker: {marker}")

    for rel in STYLE_SUPPRESSION_TARGETS:
        text = _read(root, rel)
        checks += 1
        if "documentLocalStylesSuppressed" not in text:
            details.append(f"document editor did not suppress local style block: {rel}")
        for snippet in FORBIDDEN_DOCUMENT_LOCAL_STYLE_SNIPPETS:
            checks += 1
            if snippet in text:
                details.append(f"legacy local document QSS still present in {rel}: {snippet}")

    transaction = _read(root, "alrajhi_client/features/transactions/transaction_document_tab.py")
    bottom_actions = _read(root, "alrajhi_client/features/transactions/components/transaction_bottom_actions.py")
    for marker in ("TransactionInlineHeaderBar", "TransactionLineGrid", "TransactionFooterPanel"):
        checks += 1
        if marker not in transaction:
            details.append(f"transaction document is missing visual anchor: {marker}")
    checks += 1
    if "TransactionBottomActionBar" not in bottom_actions:
        details.append("transaction bottom-actions component is missing TransactionBottomActionBar anchor")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 450,
    }


__all__ = ["phase450_unified_document_editor_visual_template_summary"]
