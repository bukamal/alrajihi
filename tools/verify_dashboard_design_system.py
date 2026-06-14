# -*- coding: utf-8 -*-
"""Verify Phase 72 dashboard remains tied to the central design system."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'dashboard_widget.py'


def main():
    text = DASHBOARD.read_text(encoding='utf-8')
    required = [
        'from theme_manager import ThemeManager',
        'from theme.brand import BRAND',
        "def _dc(key, fallback):",
        "def _dashboard_product_name():",
        "QWidget#DashboardWidget {{ background: {_dc('bg_window'",
        "stop:0 {_dc('primary'",
        "title = QLabel(_dashboard_product_name())",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit('missing dashboard design-system markers: ' + ', '.join(missing))
    banned = [
        'widget_polish',
        'installEventFilter',
        'QTWEBENGINE_CHROMIUM_FLAGS',
        '--shm-helper',
    ]
    found = [item for item in banned if item in text]
    if found:
        raise SystemExit('unsafe runtime markers found in dashboard: ' + ', '.join(found))
    print('dashboard design-system wiring ok')


if __name__ == '__main__':
    main()
