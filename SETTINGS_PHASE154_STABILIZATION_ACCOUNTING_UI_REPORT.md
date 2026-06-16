# Phase 154 - Stabilization + Accounting UI/Reports

تم التطبيق فعليًا على الكود بعد Phase 152/153.

## ما تم إصلاحه

1. إنشاء طلب اعتماد تلقائي عند إنشاء فاتورة تتجاوز حد الاعتماد.
2. ربط ذلك محليًا في `InvoiceService.create`.
3. ربط ذلك على الخادم في `POST /api/invoices`.
4. إضافة أزرار تشغيلية في شاشة الفواتير: إرسال للاعتماد، اعتماد، رفض، ترحيل، إعادة فتح.
5. إظهار حالة Workflow في جداول فواتير البيع والشراء.
6. إضافة تقارير محاسبية حقيقية مبنية على `journal_entries/journal_lines`:
   - Trial Balance
   - Account Ledger
   - Journal Entries
7. إضافة REST endpoints:
   - `GET /api/reports/accounting/trial_balance`
   - `GET /api/reports/accounting/ledger`
   - `GET /api/reports/accounting/journal_entries`
8. إضافة دوال client REST مقابلة.
9. إضافة دوال `AccountingService.trial_balance()` و `AccountingService.ledger()`.

## حدود المرحلة

هذه المرحلة لا تضيف واجهة محاسبية كاملة مستقلة بعد، لكنها تجعل التقارير والخدمات والأزرار التشغيلية موجودة ومتصلة فعليًا.
