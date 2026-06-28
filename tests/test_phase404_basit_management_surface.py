# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_base_widget_and_toolbar_mark_management_surfaces():
    base = read('alrajhi_client/views/widgets/base_widget.py')
    toolbar = read('alrajhi_client/views/widgets/components/table_toolbar.py')
    assert "basitManagementWorkspace" in base
    assert "basitListToolbar" in base
    assert "basitManagementTable" in base
    assert "self.setProperty('basitListToolbar', True)" in toolbar
    assert "basitToolbarButton" in toolbar
    assert "basitListSearch" in toolbar


def test_inline_master_detail_has_basit_surface_markers():
    responsive = read('alrajhi_client/ui/components/responsive_master_detail.py')
    inline = read('alrajhi_client/views/widgets/unified_inline_workspace.py')
    assert "basitMasterDetail" in responsive
    assert "basitMasterDetailSplitter" in responsive
    assert "basitDetailPlaceholder" in responsive
    assert "basitManagementWorkspace" in inline
    assert "basitInlineEditorPage" in inline
    assert "basitInlineEditorHost" in inline


def test_modern_widget_applies_basit_list_surface_to_custom_list_pages():
    modern = read('alrajhi_client/views/widgets/modern_ui.py')
    assert "def _apply_basit_list_surface" in modern
    assert "('table', 'cash_table', 'bank_table', 'search_edit')" in modern
    assert "_apply_basit_list_surface(widget)" in modern
    assert "basitManagementTable" in modern


def test_qss_contains_management_surface_rules():
    qss = read('alrajhi_client/theme/qss.py')
    assert "Phase404: Basit-inspired management/list workspaces" in qss
    assert 'QWidget[basitManagementWorkspace="true"]' in qss
    assert 'QWidget[basitListToolbar="true"]' in qss
    assert 'QLineEdit[basitListSearch="true"]' in qss
    assert 'QSplitter#ResponsiveMasterDetailSplitter[basitMasterDetailSplitter="true"]' in qss
    assert 'QFrame#DetailPlaceholder[basitDetailPlaceholder="true"]' in qss


def test_quality_contract_documents_scope():
    contract = read('alrajhi_client/workspace/quality/basit_management_surface_contract.py')
    assert "BASIT_MANAGEMENT_SURFACE_CONTRACT" in contract
    for surface in ('materials', 'customers', 'suppliers', 'categories', 'vouchers'):
        assert surface in contract
