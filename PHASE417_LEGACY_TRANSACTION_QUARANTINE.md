# Phase 417 — Legacy Transaction Quarantine

## الهدف

هذه المرحلة لا تضيف ميزة جديدة ولا ترقّع محرر الفاتورة القديم. الهدف هو عزل مسارات الفواتير والمرتجعات القديمة بحيث لا يمكن أن تعود إلى مسار الإنتاج بالاستيراد المباشر أو fallback غير مقصود.

## ما تغيّر

- إضافة وحدة مركزية بلا اعتماد على PyQt:
  `alrajhi_client/workspace/quality/legacy_transaction_quarantine.py`
- جعل استيراد المحولات القديمة يفشل مبكرًا قبل تحميل `InvoiceDialog` أو Dialogs المرتجعات القديمة:
  - `features.invoices.invoice_editor_tab`
  - `features.returns.return_editor_tabs`
- إزالة أي اعتماد في `main_window.py` على `allow_legacy_transaction_documents()` كمسار fallback.
- إبقاء `allow_legacy_transaction_documents()` يعيد `False` دائمًا كحاجز توافق، لكنه لم يعد يستخدم لإحياء محررات قديمة.
- توثيق الاستثناء الوحيد كاستثناء forensic يدوي عبر:
  `ALRAJHI_FORENSIC_ALLOW_LEGACY_TRANSACTION_IMPORT=1`
  وهذا مخصص للتفتيش التقني فقط، وليس لمسار تشغيل أو إعداد إنتاجي.

## القاعدة الجديدة

المحررات القديمة ليست “مسارًا احتياطيًا”. هي كود مرجعي معزول.

مسارات الإنتاج الوحيدة للفواتير والمرتجعات يجب أن تمر عبر:

- `features.transactions.documents.sales_invoice_tab.SalesInvoiceTab`
- `features.transactions.documents.purchase_invoice_tab.PurchaseInvoiceTab`
- `features.transactions.documents.sales_return_tab.SalesReturnTab`
- `features.transactions.documents.purchase_return_tab.PurchaseReturnTab`

## لماذا هذا مهم

مشاكل Enter وتكرار الصفوف ومسح الخلايا جاءت من امتزاج محرك الجداول الجديد مع طبقات قديمة تملك:

- `eventFilter` محلي.
- ترتيب أعمدة ثابت بالأرقام.
- `LinesModel` قديم.
- إضافة صفوف عبر `dataChanged`.

Phase 417 يمنع عودة هذه الطبقة إلى Runtime، وبالتالي تصبح Phase 418 قادرة على توحيد دورة حياة كل الجداول بدون منافسة من Legacy.

## التحقق

- `tools/phase417_legacy_transaction_quarantine_guard.py`
- `tests/test_phase417_legacy_transaction_quarantine.py`
- `alrajhi_client/workspace/quality/legacy_transaction_quarantine_contract.py`

## الخطوة التالية

Phase 418 يجب أن تكون: `Editable Grid Lifecycle Unification` لتعميم سياسة الصفوف والتنقل على الشراء، المرتجعات، التصنيع، التحويلات، ووحدات المادة.
