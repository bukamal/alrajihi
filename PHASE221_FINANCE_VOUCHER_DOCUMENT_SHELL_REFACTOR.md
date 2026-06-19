# Phase 221 — Finance Voucher Document Shell Refactor

## هدف المرحلة

إعادة بناء واجهة سندات القبض/الدفع لتصبح Finance Document Shell حقيقيًا، لا مجرد نموذج حقول داخل تبويب. هذه المرحلة تكمل ما بدأ في Phase 220 مع العميل/المورد، وتقرّب السندات من نفس فلسفة مستندات الفواتير: Header، جسم مستند، ملخص جانبي، وشريط أوامر سفلي.

## الملفات الأساسية

- `alrajhi_client/features/vouchers/voucher_editor_tab.py`
- `alrajhi_client/features/finance/documents/expense_document_tab.py`
- `alrajhi_client/i18n/translator.py`
- `tools/phase221_voucher_document_shell_guard.py`
- `tools/phase219_projectwide_architecture_audit.py`

## ما تغير

أصبح `VoucherEditorTab` يحتوي على:

- `DocumentHeaderCard`
- `DocumentPanel`
- `SummaryPanel`
- `BottomActionBar`
- بطاقات مالية صغيرة عبر `_VoucherMetricCard`

والأجزاء الوظيفية بقيت خلف الخدمات والسياسات نفسها:

- الحفظ عبر `voucher_service.add/update`
- الطباعة والتصدير عبر `printing_service`
- الصلاحيات والإعدادات عبر `finance_operation_policy`
- العملة عبر `currency.format_base_amount`, `to_display`, `from_display`

## ExpenseDocumentTab

بقي `ExpenseDocumentTab` يرث من `VoucherEditorTab`، لكنه صار يستفيد من Finance Document Shell الجديد، مع إبقاء نوع المستند ثابتًا كـ `expense` وعمليات الصلاحيات الخاصة بالمصاريف:

- `OP_EXPENSE_CREATE`
- `OP_EXPENSE_EDIT`
- `OP_EXPENSE_PRINT`

## الفحوص

تم تشغيل:

```bash
python tools/phase221_voucher_document_shell_guard.py
python tools/phase219_projectwide_architecture_audit.py
python tools/reports_contract_check.py
python tools/phase212_runtime_stabilization_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

## النتيجة

سندات القبض والدفع لم تعد form-stack UI. أصبحت مستندًا ماليًا موحدًا أقرب إلى واجهة الفواتير، مع ملخص ودفع وربط طرف/فاتورة وشريط أوامر ثابت.
