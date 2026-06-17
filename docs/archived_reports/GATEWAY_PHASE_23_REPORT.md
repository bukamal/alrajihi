# Gateway Phase 23 Report — Inventory Ledger Shadow Posting

## الهدف
ربط `Inventory Ledger` بحركات الفواتير كـ Shadow Posting فقط، بدون تغيير حساب الرصيد الحالي وبدون جعل ledger مصدر الحقيقة بعد.

## ما تم تنفيذه

### Client / Local Mode
- تم تعديل `WarehouseService.record_invoice_movements()` ليقوم بتسجيل:
  - حركة المستودع الحالية كما هي.
  - قيد موازي في `inventory_ledger`.
- تم تعديل `WarehouseService.reverse_invoice_movements()` ليقبل بيانات الفاتورة القديمة ويسجل قيود عكسية في `inventory_ledger` عند تعديل/حذف الفاتورة.
- تم تعديل `InvoiceService.update()` و `InvoiceService.delete()` لتمرير بيانات الفاتورة القديمة إلى عملية العكس.

### Server / Remote Mode
- تم تعديل `alrajhi_server/api/invoices.py` لإضافة helper functions:
  - `_post_inventory_ledger_entry()`
  - `_post_invoice_ledger_entries()`
  - `_post_invoice_ledger_reversal()`
- عند إنشاء فاتورة عبر API يتم تسجيل قيود ledger موازية.
- عند تعديل فاتورة عبر API يتم تسجيل قيود عكسية للفاتورة القديمة ثم قيود جديدة.
- عند حذف فاتورة عبر API يتم تسجيل قيود عكسية قبل soft delete.

## حدود المرحلة
- لم يتم تغيير طريقة حساب `items.quantity`.
- لم يتم تغيير `inventory_movements`.
- لم يتم تغيير `item_warehouse_balances`.
- لم يتم اعتماد `inventory_ledger` كمصدر نهائي للرصيد.

## الفحوصات
- `architecture_guard`: ناجح.
- `compileall`: ناجح.
- `zip test`: ناجح.
- اختبار helper functions للسيرفر عبر SQLite in-memory: ناجح.

## ملاحظات اختبارية
بيئة الفحص لا تحتوي Flask/PyQt5، لذلك لم يتم تشغيل الواجهة أو الخادم فعلياً داخل البيئة. تم الاعتماد على فحص static/compile واختبار helpers بمعزل عن Flask.

## المخاطر المتبقية
- يجب اختبار إنشاء/تعديل/حذف فواتير شراء وبيع فعلياً في Local وClient mode.
- في هذه المرحلة قد توجد فروقات بين ledger والرصيد القديم إذا كانت هناك فواتير قديمة قبل Phase 23. هذا متوقع لأن المرحلة Shadow Posting تبدأ من العمليات الجديدة فقط.

## الخطوة التالية المقترحة
Phase 24: شاشة/تقرير مقارنة بين الرصيد الحالي و`ledger_balance` بدون تعديل أي بيانات.
