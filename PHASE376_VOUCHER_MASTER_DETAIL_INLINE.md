# Phase 376 — Voucher Master-Detail Inline Editor

## الهدف
توحيد واجهة السندات مع هيكلية العملاء والموردين: قائمة رئيسية مع لوحة تفاصيل/تحرير جانبية داخل نفس التبويب، بدلاً من تبديل التبويب بالكامل إلى صفحة تحرير منفصلة أو فتح تبويب جديد.

## التغييرات
- تحويل `VouchersWidget` إلى `ResponsiveMasterDetail` مثل `CustomersWidget` و`SuppliersWidget`.
- إضافة `DetailPlaceholder` لعرض ملخص السند المحدد.
- جعل محرر سند القبض وسند الدفع وسند المصروف يظهر في `detail_stack` داخل نفس تبويب السندات.
- إبقاء القائمة والبحث والفلاتر ظاهرة أثناء التحرير.
- منع أزرار الإضافة/التعديل داخل قائمة السندات من استخدام مسارات فتح التبويبات.
- الاحتفاظ بسند المصروف عبر `ExpenseDocumentTab` وسند القبض/الدفع عبر `VoucherEditorTab`.

## الحوكمة
- أضيف عقد الجودة `voucher_master_detail_inline_contract.py`.
- أضيف guard: `tools/phase376_voucher_master_detail_inline_guard.py`.
- أضيفت اختبارات: `tests/test_phase376_voucher_master_detail_inline.py`.
