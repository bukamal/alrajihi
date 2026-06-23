# PHASE 374 — Specialized Interface Menu & Material Entry Focus

## الهدف
- نقل واجهات المطعم، المقهى، والألبسة إلى زر واحد في شريط القوائم باسم مناسب لهذه الواجهات.
- منع جداول التحرير من بدء التحرير في أول عمود أو الباركود عندما يكون عمود المادة موجوداً.

## التغييرات
- إعادة تسمية زر Quick Actions إلى `واجهات النشاط / Industry interfaces / Branchenoberflächen`.
- حصر هذا الزر في:
  - `واجهة المطعم`
  - `واجهة المقهى`
  - `واجهة الألبسة`
- إزالة التكرار من شريط القوائم الرئيسي:
  - لا قائمة مستقلة للمطعم.
  - لا قائمة مستقلة للمقهى.
  - لا تكرار للألبسة تحت المخزون.
- ترتيب أولوية جداول التحرير أصبح:
  1. item/material
  2. product
  3. barcode
- جعل عمود الرقم `row/#` غير قابل للتحرير في فواتير البيع والشراء.

## ملفات الحماية
- `tools/phase374_special_interface_menu_entry_focus_guard.py`
- `tests/test_phase374_special_interface_menu_entry_focus.py`
- `alrajhi_client/workspace/quality/special_interface_menu_entry_focus_contract.py`
