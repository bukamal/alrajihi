# -*- coding: utf-8 -*-
"""Guard for Phase 65 design-system foundation."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'

REQUIRED = [
    CLIENT / 'theme' / '__init__.py',
    CLIENT / 'theme' / 'brand.py',
    CLIENT / 'theme' / 'qss.py',
    CLIENT / 'theme_manager.py',
    CLIENT / 'ui' / 'design_system.py',
]


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        raise SystemExit('missing design-system files: ' + ', '.join(missing))

    brand = (CLIENT / 'theme' / 'brand.py').read_text(encoding='utf-8')
    for token in ('LIGHT_TOKENS', 'DARK_TOKENS', '#0F3D75', '#1E5AA8', '#2D7FF9'):
        if token not in brand:
            raise SystemExit(f'missing brand token: {token}')

    manager = (CLIENT / 'theme_manager.py').read_text(encoding='utf-8')
    for snippet in ('from theme.brand import get_tokens', 'from theme.qss import build_global_qss'):
        if snippet not in manager:
            raise SystemExit(f'theme manager is not wired to design system: {snippet}')

    qss = (CLIENT / 'theme' / 'qss.py').read_text(encoding='utf-8')
    for selector in ('QToolBar', 'QTableView', 'QPushButton#primary', 'QFrame#brandCard'):
        if selector not in qss:
            raise SystemExit(f'missing global QSS selector: {selector}')

    print('OK design-system foundation is wired')


if __name__ == '__main__':
    main()
