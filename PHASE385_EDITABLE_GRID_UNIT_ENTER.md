# PHASE385_EDITABLE_GRID_UNIT_ENTER

## الهدف
تثبيت مسار التنقل داخل الجداول التحريرية بحيث لا يتجاوز النظام عمود الوحدة بعد اختيار المادة أو إدخال الباركود.

## التغيير
- أصبح مسار Enter بعد تثبيت المادة أو الباركود:
  - المادة / الباركود
  - الوحدة
  - الكمية
- إذا كان عمود الوحدة مخفيًا أو غير قابل للتحرير، يعود النظام إلى الكمية كمسار احتياطي.
- لا يتم مسح الحقول أثناء التنقل؛ يتم تحديد النص فقط لتسهيل الاستبدال عند إدخال قيمة جديدة.

## الملفات
- `alrajhi_client/ui/table_keyboard_policy.py`
- `alrajhi_client/workspace/quality/editable_grid_unit_enter_contract.py`
- `tools/phase385_editable_grid_unit_enter_guard.py`
- `tests/test_phase385_editable_grid_unit_enter.py`

## التحقق
- يحمي الحارس أن يتم فحص عمود الوحدة قبل الكمية في `_standard_post_commit_index`.
- يحمي أن تبقى مخططات المبيعات، المشتريات، المرتجعات، التحويلات، وBOM مرتبة بوحدة قبل الكمية.
