# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
files = [
    ROOT / 'alrajhi_client/views/widgets/items_widget.py',
    ROOT / 'alrajhi_client/views/dialogs/item_dialog.py',
    ROOT / 'alrajhi_client/views/widgets/warehouses_widget.py',
]
required_keys = [
    'items_search_placeholder','item_name_header','default_unit_header','all_categories','stock_item_type',
    'item_add_title','item_edit_title','item_data_title','basic_data','purchase_price','selling_price',
    'reorder_level','sub_units_group','warehouse_management','warehouse_hint','warehouses_search',
    'balances_tab','movements_tab','transfers_tab','warehouse_transfer_dialog','execute_transfer',
]

def main():
    errors = []
    for p in files:
        txt = p.read_text(encoding='utf-8')
        try:
            ast.parse(txt)
        except SyntaxError as e:
            errors.append(f'Syntax error in {p}: {e}')
        if 'translate(' not in txt:
            errors.append(f'Missing translate() usage in {p}')
    # Load translator using source path only.
    import sys
    sys.path.insert(0, str(ROOT / 'alrajhi_client'))
    from i18n import translate, set_language
    for lang in ('ar','de','en'):
        set_language(lang)
        for key in required_keys:
            if translate(key) == key:
                errors.append(f'Missing translation {lang}:{key}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('OK phase79 inventory/items/warehouse localization guard passed')

if __name__ == '__main__':
    main()
