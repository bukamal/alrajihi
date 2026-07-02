# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_master_detail_shell_exists():
    text = (ROOT / 'alrajhi_client/ui/components/responsive_master_detail.py').read_text(encoding='utf-8')
    assert 'class ResponsiveMasterDetail' in text
    assert 'QSplitter(Qt.Horizontal' in text
    assert 'class DetailPlaceholder' in text


def test_customers_suppliers_use_master_detail():
    for rel in ['alrajhi_client/views/widgets/customers_widget.py', 'alrajhi_client/views/widgets/suppliers_widget.py']:
        text = (ROOT / rel).read_text(encoding='utf-8')
        # Phase376/458: the concrete list widgets install the shared
        # master-detail shell through PartyInlineEditorHostMixin.
        assert 'PartyInlineEditorHostMixin' in text
        assert '_install_party_inline_host' in text
        assert '_update_detail_preview' in text
    host = (ROOT / 'alrajhi_client/views/widgets/party_inline_editor_host.py').read_text(encoding='utf-8')
    shared = (ROOT / 'alrajhi_client/views/widgets/unified_inline_workspace.py').read_text(encoding='utf-8')
    assert 'UnifiedInlineWorkspaceMixin' in host
    assert 'ResponsiveMasterDetail' in shared
    assert 'DetailPlaceholder' in shared


def test_item_editor_is_responsive_splitter():
    text = (ROOT / 'alrajhi_client/features/items/item_editor_tab.py').read_text(encoding='utf-8')
    assert 'QSplitter' in text
    assert 'ItemEditorResponsiveSplitter' in text
    assert 'setStretchFactor' in text
