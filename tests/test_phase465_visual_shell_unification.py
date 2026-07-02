# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_phase465_visual_shell_helper_exists_and_is_presentation_only():
    helper = _read('alrajhi_client/ui/visual_shell.py')
    assert 'PHASE = 465' in helper
    assert 'def apply_standard_modal_chrome' in helper
    assert 'def mark_visual_shell' in helper
    assert 'def set_widgets_visible' in helper
    forbidden = ('DatabaseConnection', 'sqlite3', '.execute(', 'requests.', 'urllib')
    assert not any(token in helper for token in forbidden)


def test_phase465_change_password_uses_standard_modal_chrome():
    change = _read('alrajhi_client/views/dialogs/change_password_dialog.py')
    assert "apply_standard_modal_chrome(self, role='change_password', allow_minimize=False)" in change
    assert 'ChangePasswordIntro' in change
    assert 'self.resize(560, 460)' in change
    assert 'StandardModalActionsLayout' in change


def test_phase465_login_splash_and_pos_are_marked():
    login = _read('alrajhi_client/views/dialogs/login_dialog.py')
    splash = _read('alrajhi_client/views/splash_screen.py')
    pos = _read('alrajhi_client/views/widgets/pos_widget.py')
    assert "self.main_frame.setProperty('visualShellPhase', 465)" in login
    assert "mark_visual_shell(self.main_frame, surface='login', shell_type='login')" in login
    assert 'self.min_btn.setVisible(False)' in login
    assert 'startupCollisionPolicy' in splash
    assert 'mark_visual_shell(self.container, surface="startup_splash", shell_type="startup")' in splash
    assert "mark_visual_shell(self, surface='pos', shell_type='operational')" in pos
    assert 'operationalFullscreenActive' in pos
    assert 'set_widgets_visible((getattr(self, \'top_tools_frame\', None), getattr(self, \'pos_hint_label\', None)), not bool(active))' in pos


def test_phase465_qss_contracts_generate_without_name_errors():
    qss_source = _read('alrajhi_client/theme/qss.py')
    for marker in (
        'Phase465: Visual shell unification and collision fixes',
        'QFrame#BrandDialogFrame[visualShellPhase="465"]',
        'QFrame#LoginRuntimeTitleBar[visualShellPhase="465"]',
        'QFrame#brandedStartupCard[visualShellPhase="465"]',
        'QWidget#posWidget[operationalFullscreenActive="true"]',
    ):
        assert marker in qss_source

    import sys
    sys.path.insert(0, str(ROOT / 'alrajhi_client'))
    from theme.brand import get_tokens
    from theme.qss import build_global_qss

    qss = build_global_qss(get_tokens('light'))
    assert 'Phase465' in qss
    assert 'visualShellPhase="465"' in qss
