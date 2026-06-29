# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.unified_document_editor_visual_template_contract import phase450_unified_document_editor_visual_template_summary


def test_phase450_document_visual_template_ready():
    summary = phase450_unified_document_editor_visual_template_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_document_qss_order_and_core_roles():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert qss.find("Phase450: unified document editor visual template") > qss.find("Phase449: reports workspace visual refactor")
    assert 'QWidget[documentVisualTemplatePhase="450"]' in qss
    assert 'QTableView[visualRole="document_table"]' in qss
    assert 'QPushButton[visualRole="document_primary_action"]' in qss


def test_document_layout_policy_applies_visual_metadata():
    policy = (ROOT / "alrajhi_client/workspace/documents/document_layout_policy.py").read_text(encoding="utf-8")
    assert "_apply_document_visual_template(widget, kind=resolved_kind)" in policy
    assert 'widget.setProperty("documentVisualTemplatePhase", 450)' in policy
    assert 'widget.setProperty("visualWorkspaceType", "document")' in policy
    assert '"document_primary_action"' in policy


def test_legacy_document_local_styles_are_suppressed():
    files = [
        "alrajhi_client/features/vouchers/voucher_editor_tab.py",
        "alrajhi_client/features/parties/party_editor_tab.py",
        "alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py",
        "alrajhi_client/features/manufacturing/bom_document_tab.py",
    ]
    for rel in files:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "documentLocalStylesSuppressed" in text
        assert "QFrame#DocumentHeaderCard, QFrame#FormCard" not in text
        assert "QFrame#DocumentHeaderCard, QFrame#DocumentPanel" not in text
