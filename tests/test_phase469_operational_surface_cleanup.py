from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_phase469_floating_surface_is_opaque_before_qss_application():
    helper = read('alrajhi_client/ui/floating_quick_create.py')
    panel = read('alrajhi_client/ui/inline_quick_create.py')
    qss = read('alrajhi_client/theme/qss.py')
    assert 'floatingSurfacePhase", "469"' in helper
    assert 'panel.setProperty("floatingQuickCreate", "true")' in helper
    assert 'Qt.WA_NoSystemBackground, False' in helper
    assert 'panel.setWindowOpacity(1.0)' in helper
    assert 'object_selector = f"QFrame#{panel.objectName()}"' in helper
    assert 'panel.style().unpolish(panel)' in helper
    assert 'floatingSurfacePhase", "469"' in panel
    assert 'floatingLayoutSafe' in panel
    assert 'opacity: 1' in qss
    assert 'hard opaque floating cards' in qss


def test_phase469_pos_is_compact_and_drawer_stays_below_scan_bar():
    pos = read('alrajhi_client/views/widgets/pos_widget.py')
    payment = read('alrajhi_client/features/pos/pos_payment_shell.py')
    assert "posOperationalCleanupPhase', 469" in pos
    assert "pos_operational_scan_height_phase469" in pos
    assert "pos_table_min_height_phase469" in pos
    assert "posPaymentCompactPhase', 469" in pos
    assert 'anchored floating drawer below scan bar' in pos
    assert 'scan_bottom = self.scan_frame.y() + self.scan_frame.height() + margin' in pos
    assert 'x = max(margin, self.width() - width - margin)' in pos
    assert 'POSQuickCreateDrawer_item' in pos
    assert 'layout.addWidget(self.inline_item_panel)' not in pos
    assert 'posPaymentCompactPhase", 469' in payment
    assert 'header.setVisible(False)' in payment
    assert 'one compact action row' in payment
    assert 'actions.addWidget(button, 0, index)' in payment


def test_phase469_restaurant_header_is_split_and_less_crowded():
    src = read('alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py')
    assert 'restaurantOperationalCleanupPhase", 469' in src
    assert 'split the restaurant operation header' in src
    assert 'title_row = QHBoxLayout()' in src
    assert 'search_row = QHBoxLayout()' in src
    assert 'action_row = QHBoxLayout()' in src
    assert 'search_row.addWidget(self.search_edit, 1)' in src
    assert 'action_row.addWidget(self.quick_category_btn)' in src
    assert 'action_row.addWidget(self.quick_item_btn)' in src
    assert 'header.addLayout(search_row)' in src
    assert 'header.addLayout(action_row)' in src


def test_phase469_qss_targets_operational_surfaces():
    qss = read('alrajhi_client/theme/qss.py')
    assert 'QWidget#posWidget[posOperationalCleanupPhase="469"] QFrame#POSRuntimeContextBar' in qss
    assert 'QWidget#posWidget[posOperationalCleanupPhase="469"] QWidget#posPaymentShell[posPaymentCompactPhase="469"]' in qss
    assert 'QWidget#restaurantSimplePOSWidget[restaurantOperationalCleanupPhase="469"] QFrame#restaurantSimpleHeaderCard' in qss
