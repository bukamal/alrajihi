# -*- coding: utf-8 -*-
"""Phase 59 guard: responsive master-detail and enterprise table UX.

This guard is intentionally structural. It verifies that the management pages
which users resize all day use a splitter-based master/detail shell and that the
item editor no longer behaves like a fixed-width form row.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SNIPPETS = {
    'alrajhi_client/ui/components/responsive_master_detail.py': [
        'class ResponsiveMasterDetail',
        'QSplitter(Qt.Horizontal',
        'DetailPlaceholder',
    ],
    'alrajhi_client/views/widgets/customers_widget.py': [
        'ResponsiveMasterDetail',
        'DetailPlaceholder',
        '_update_detail_preview',
    ],
    'alrajhi_client/views/widgets/suppliers_widget.py': [
        'ResponsiveMasterDetail',
        'DetailPlaceholder',
        '_update_detail_preview',
    ],
    'alrajhi_client/features/items/item_editor_tab.py': [
        'QSplitter',
        'ItemEditorResponsiveSplitter',
        'setStretchFactor',
    ],
    'alrajhi_client/ui/smart_table_view.py': [
        'setSectionsMovable(True)',
        'set_column_visible',
        'fit_columns_to_view',
        'save_layout',
    ],
}


def main() -> int:
    errors: list[str] = []
    for rel, snippets in REQUIRED_SNIPPETS.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f'missing {rel}')
            continue
        text = path.read_text(encoding='utf-8')
        for snippet in snippets:
            if snippet not in text:
                errors.append(f'{rel}: missing {snippet!r}')
    if errors:
        print('Phase 59 master-detail UX guard failed:')
        for err in errors:
            print(f' - {err}')
        return 1
    print('Phase 59 master-detail UX guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
