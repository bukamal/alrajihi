# Phase 163 — Transaction Document Edit Mode

## الهدف
تحويل `TransactionDocumentTab` من pilot لإنشاء فاتورة جديدة فقط إلى محرر فعلي قادر على فتح فاتورة موجودة، تعديلها، وحفظها عبر `invoice_service.update()` مع المحافظة على fallback إلى `InvoiceDialog` عند تعطيل feature flags.

## ما تغير

### 1. ربط التعديل بالواجهة الجديدة
تم تحديث `MainWindow.open_quick_invoice()` ليستخدم مستندات `features.transactions.documents` في حالتين:

- إنشاء فاتورة جديدة.
- فتح فاتورة موجودة عند تفعيل `features/use_new_transaction_documents_for_existing`.

في حال فشل الاستيراد أو تعطيل الخيار، يعود النظام تلقائيًا إلى `InvoiceEditorTab` القديم.

### 2. تحميل فاتورة موجودة
أضيف إلى `TransactionDocumentTab`:

- `load_invoice_data(invoice_id)`
- تحميل العميل/المورد.
- تحميل التاريخ والمرجع والملاحظات.
- تحميل المستودع.
- تحميل المدفوع.
- تحميل سطور الفاتورة داخل `TransactionLineModel`.
- تحديث عنوان التبويب بعد التحميل.

### 3. دعم update
أصبح `workspace_save()` يختار المسار الصحيح:

- `invoice_service.create(payload)` عند عدم وجود `invoice_id`.
- `invoice_service.update(invoice_id, payload)` عند فتح فاتورة موجودة.

### 4. مستودع ودفع وملخص فعلي
أضيفت عناصر واجهة أساسية:

- `warehouse_combo`
- `paid_spin`
- subtotal
- discount
- tax
- remaining
- net total

ويتم إرسال `warehouse_id`, `paid_amount`, `paid`, و `remaining` ضمن payload.

### 5. تحسين نموذج السطور
تم توسيع `TransactionLineModel` ليشمل:

- `load_invoice_lines()`
- `clear()`
- حساب subtotal / discount / tax / total
- حفظ batch/expiry عند وجودها
- تحويل السطور إلى payload متوافق مع `invoice_service`

### 6. تصحيح PyQt5
تمت إزالة بقايا `PySide6` من طبقة `transactions` الجديدة، واستبدالها بـ `PyQt5`.

## Feature flags

```text
features/use_new_transaction_documents = true
features/use_new_transaction_documents_for_existing = true
```

## حدود المرحلة

- الطباعة لا تزال fallback/placeholder داخل `workspace_print()` في `BaseDocumentTab`.
- لا توجد delegates احترافية بعد لاختيار الصنف والوحدة داخل خلايا الجدول.
- الدفع هنا قيمة مدفوعة داخل الفاتورة فقط، وليس سند قبض/دفع منفصل.
- المرتجعات و POS والمطعم لم تُنقل بعد إلى نفس engine.

## القرار المعماري
لا يزال `invoice_dialog.py` legacy fallback. لا ينبغي إضافة خصائص جديدة إليه إلا لإصلاح أعطال حرجة.
