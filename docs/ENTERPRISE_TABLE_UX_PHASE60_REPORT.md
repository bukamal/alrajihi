# Phase 60 — Enterprise Table UX

## هدف المرحلة
تحويل `SmartTableView` من جدول موحد بسيط إلى جدول ERP احترافي يدعم إدارة الأعمدة، التكيّف مع حجم النافذة، حفظ التخطيط، والطباعة/التصدير عبر المسار الموحد.

## المنجز
- إضافة `ColumnChooserDialog` موحد لكل الجداول.
- دعم إظهار/إخفاء الأعمدة من واجهة واحدة.
- منع إخفاء آخر عمود حتى لا يصبح الجدول فارغًا بصريًا.
- تعزيز حفظ ترتيب/حجم/إخفاء الأعمدة عبر `TablePreferences`.
- إضافة `export_to_pdf()` و`print_preview()` كواجهات موحدة فوق `print_table()`.
- إضافة `set_layout_profile()` كتمهيد لتخطيطات حسب المستخدم/الدور لاحقًا.
- توسيع `TableToolbar` لدعم:
  - Column chooser
  - Fit columns
  - Responsive columns
  - Export PDF
- تثبيت identities لجداول حرجة في المخزون، السندات، التصنيع، التدقيق، التصنيفات.
- إضافة guard جديد: `tools/enterprise_table_ux_guard.py`.

## قيود مقصودة
لم يتم تحويل جداول الإدخال التحريرية الحساسة مثل POS وبعض جداول المرتجعات الداخلية إلى سلوك إدارة أعمدة كامل، لأنها ليست جداول قراءة/إدارة بل جداول إدخال مباشر.

## التحقق
- `architecture_guard`: نجح.
- `phase32_invoice_flow_guard`: نجح.
- `phase32_windows_import_guard`: نجح.
- `restaurant_production_readiness_guard`: نجح.
- `smart_table_rollout_guard`: نجح.
- `ui_consistency_guard`: نجح.
- `invoice_grid_ux_guard`: نجح.
- `master_detail_ux_guard`: نجح.
- `enterprise_table_ux_guard`: نجح.
- `unified_printing_guard`: نجح.
- `pytest`: 97 passed.
- `compileall`: نجح.
