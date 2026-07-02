from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_phase466_global_action_bar_is_utility_only():
    registry = read('alrajhi_client/workspace/registry/ui_manifest.py')
    action_bar = read('alrajhi_client/shell/unified_action_bar.py')
    assert 'GLOBAL_UTILITY_ACTIONS: tuple[str, ...] = ("refresh", "theme", "screenshot", "fullscreen", "user")' in registry
    assert 'return GLOBAL_UTILITY_ACTIONS' in registry
    assert 'allowed = {"refresh", "theme", "screenshot", "fullscreen", "user"}' in action_bar
    assert 'self.context_label.setVisible(False)' in action_bar
    assert 'New/Save/Print/Export/Quick Open are intentionally hidden globally' in action_bar


def test_phase466_fullscreen_exit_overlay_is_always_cleared():
    controller = read('alrajhi_client/ui/operational_fullscreen_controller.py')
    assert 'self._exit_button.hide()' in controller
    assert 'if not self._active:' in controller
    assert 'returning early would leave the red' in controller
    assert 'QTimer.singleShot(80, self._exit_button.hide)' in controller
    assert 'else:\n            try:\n                self._exit_button.hide()' in controller


def test_phase466_pos_quick_create_is_floating_drawer_not_inline_stack():
    pos = read('alrajhi_client/views/widgets/pos_widget.py')
    assert 'POSQuickCreateDrawer_cashbox' in pos
    assert 'POSQuickCreateDrawer_item' in pos
    assert 'quickCreateSurface", "floating_drawer"' in pos
    assert 'layout.addWidget(self.inline_cashbox_panel)' not in pos
    assert 'layout.addWidget(self.inline_item_panel)' not in pos
    assert 'def _show_pos_quick_create_drawer' in pos
    assert 'below the scan bar' in pos
    assert 'self._position_pos_quick_create_drawer(panel)' in pos


def test_phase466_pos_top_chrome_does_not_stack_above_scan():
    pos = read('alrajhi_client/views/widgets/pos_widget.py')
    assert 'top_tools_frame.setVisible(False)' in pos
    assert 'self.pos_hint_label.setVisible(False)' in pos
    assert 'set_widgets_visible((getattr(self, \'top_tools_frame\', None), getattr(self, \'pos_hint_label\', None)), False)' in pos
