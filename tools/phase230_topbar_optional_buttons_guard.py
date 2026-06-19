# -*- coding: utf-8 -*-
"""Phase 230 guard: removed top-bar buttons must not be connected via hasattr().

ModernTopBar may keep compatibility attributes such as refresh_btn = None after
UI simplification. hasattr() returns True for those placeholders and causes a
startup crash when .clicked is accessed. The shell must connect optional buttons
only after checking that the object is not None.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
main = ROOT / 'alrajhi_client' / 'views' / 'main_window.py'
text = main.read_text(encoding='utf-8')

for forbidden in (
    "self.top_bar.refresh_btn.clicked.connect",
    "self.top_bar.screenshot_btn.clicked.connect",
    "if hasattr(self.top_bar, 'refresh_btn'):",
    'if hasattr(self.top_bar, "refresh_btn"):',
):
    if forbidden in text:
        raise AssertionError(f'Unsafe optional top-bar button binding remains: {forbidden}')

required = (
    "refresh_btn = getattr(self.top_bar, 'refresh_btn', None)",
    'if refresh_btn is not None:',
)
missing = [needle for needle in required if needle not in text]
if missing:
    raise AssertionError(f'Missing safe optional top-bar button binding patterns: {missing}')

# Phase 234 moved screenshot to UnifiedActionBar; it should no longer be wired
# through the hidden compatibility top bar.
if "screenshot_btn = getattr(self.top_bar, 'screenshot_btn', None)" in text:
    raise AssertionError('Screenshot must be bound from UnifiedActionBar, not hidden ModernTopBar')
if 'utility_bar.screenshot_btn.clicked.connect(self.export_screenshot)' not in text:
    raise AssertionError('Missing UnifiedActionBar screenshot binding')

modern = (ROOT / 'alrajhi_client' / 'views' / 'modern_topbar.py').read_text(encoding='utf-8')
if 'self.refresh_btn = None' not in modern:
    raise AssertionError('ModernTopBar compatibility placeholder refresh_btn = None changed; review main_window guard')

print('phase230 topbar optional buttons guard passed')
