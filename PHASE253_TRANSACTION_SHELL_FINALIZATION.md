# PHASE253_TRANSACTION_SHELL_FINALIZATION

## الهدف

تثبيت فواتير البيع، فواتير الشراء، مرتجع البيع، ومرتجع الشراء كعائلة
Transaction Shell رسمية واحدة بدل بقاء الاختيار بين المسار الحديث ومسارات
legacy القديمة بشكل صامت.

## ما تم

- إضافة `features.transactions.transaction_shell_contract` كعقد Qt-free لمسارات
  الفواتير والمرتجعات.
- ربط كل نوع مستند Transaction بـ `DocumentDescriptor` من Phase 249.
- توثيق المسار الرسمي لكل من:
  - `SalesInvoiceTab`
  - `PurchaseInvoiceTab`
  - `SalesReturnTab`
  - `PurchaseReturnTab`
- جعل legacy adapters اختيارية فقط عبر:
  - `features/allow_legacy_transaction_documents`
  - `ALRAJHI_ALLOW_LEGACY_TRANSACTION_DOCUMENTS`
- تعديل `MainWindow.open_quick_invoice` و `MainWindow.open_return_document` بحيث
  يحاولان TransactionDocumentTab أولًا، ولا يسقطان إلى legacy إلا إذا كان
  fallback مفعّلًا صراحة.
- تعليم `InvoiceEditorTab` و return adapters كـ legacy emergency adapters.

## الشبكة و API

العقد يؤكد أن الفواتير والمرتجعات مرتبطة بـ API واضح:

- `/api/invoices`
- `/api/returns/sales`
- `/api/returns/purchase`

وبـ remote gateways واضحة، مع استمرار حراسة Phase 250 للـ update parity.

## اللغة والعملة والصلاحيات

لم يتم إنشاء نظام لغة أو عملة جديد. هذه المرحلة تربط Transaction Shell بالعقود
الموجودة:

- `DocumentDescriptor.i18n_scope`
- `DocumentDescriptor.settings_scope`
- `DocumentPermissionBinder`
- `MoneyDisplayPolicy`
- `TransactionPrintingBridge`

## النتيجة

أصبحت عائلة الفواتير والمرتجعات رسمية وقابلة للفحص بعقد واحد. الواجهات القديمة
لم تُحذف من المشروع بعد، لكنها لم تعد fallback صامتًا؛ استعمالها يحتاج تفعيلًا
صريحًا لأغراض الطوارئ فقط.
