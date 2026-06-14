# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / 'alrajhi_client/views/dialogs/add_entity_dialog.py',
    ROOT / 'alrajhi_client/views/dialogs/change_password_dialog.py',
    ROOT / 'alrajhi_client/views/widgets/customers_widget.py',
    ROOT / 'alrajhi_client/views/widgets/suppliers_widget.py',
]
FORBIDDEN = [
    'إظهار كلمات المرور', 'قوة كلمة المرور:', 'جميع الحقول مطلوبة',
    'كلمتا المرور غير متطابقتين', 'كلمة المرور ضعيفة جدًا',
    'كلمة المرور الحالية غير صحيحة', 'إضافة عميل/مورد', 'تمت الإضافة',
    'الهاتف (اختياري)', 'العنوان (اختياري)'
]
REQUIRED_KEYS = [
    'add_customer_title','add_supplier_title','phone_optional','address_optional','add_done',
    'show_passwords','password_strength_empty','password_strength_value','password_hint',
    'password_strength_very_weak','password_strength_weak','password_strength_medium',
    'password_strength_good','password_strength_strong','all_fields_required',
    'password_too_weak','current_password_incorrect'
]

def main():
    errors = []
    for path in TARGETS:
        text = path.read_text(encoding='utf-8')
        ast.parse(text)
        for token in FORBIDDEN:
            if token in text:
                errors.append(f'{path.relative_to(ROOT)} still contains literal: {token}')
    translator = (ROOT / 'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')
    for key in REQUIRED_KEYS:
        if key not in translator:
            errors.append(f'missing translation key: {key}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('OK phase93 customer/supplier/password dialog localization')

if __name__ == '__main__':
    main()
