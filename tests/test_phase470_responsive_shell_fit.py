# -*- coding: utf-8 -*-
"""Phase470 responsive shell and floating quick-create regression guards."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_table_toolbar_is_two_row_responsive_not_single_overflow_row():
    text = read("alrajhi_client/views/widgets/components/table_toolbar.py")
    assert "responsiveToolbarPhase" in text
    assert "QVBoxLayout" in text
    assert "TableToolbarActionRow" in text
    assert "TableToolbarSearchRow" in text
    assert "layout.addLayout(action_row)" in text
    assert "layout.addLayout(search_row)" in text


def test_material_filters_are_grid_cells_not_one_long_hbox():
    text = read("alrajhi_client/views/widgets/items_widget.py")
    assert "QGridLayout" in text
    assert "materialsFilterGridPhase" in text
    assert "MaterialsFilterCell" in text
    assert "add_pair(translate('row_density'), self.density_filter)" in text
    assert "filter_layout.addStretch()" not in text


def test_floating_quick_create_forms_scroll_and_stay_solid():
    inline = read("alrajhi_client/ui/inline_quick_create.py")
    floating = read("alrajhi_client/ui/floating_quick_create.py")
    assert "QScrollArea" in inline
    assert "InlineQuickCreateFormScroll" in inline
    assert "InlineQuickCreateFormHolder" in inline
    assert "floatingSurfacePhase", "470"
    assert "panel.setAttribute(Qt.WA_TranslucentBackground, False)" in floating
    assert "panel.setAutoFillBackground(True)" in floating
    assert "anchor_pos = _anchor_point(panel, anchor)" in floating
    assert "window.height() - y - margin" in floating


def test_qss_has_phase470_visual_contracts():
    qss = read("alrajhi_client/theme/qss.py")
    assert 'QWidget[responsiveToolbarPhase="470"]' in qss
    assert 'QFrame#MaterialsFilterCard[materialsFilterGridPhase="470"]' in qss
    assert 'QFrame#MaterialsFilterCell[materialsFilterCellPhase="470"]' in qss
    assert 'QScrollArea#InlineQuickCreateFormScroll' in qss
