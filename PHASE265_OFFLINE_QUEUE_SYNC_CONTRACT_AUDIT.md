# PHASE 265 — Offline Queue / Sync Contract Audit

## الهدف
توحيد سياسة العمل عند انقطاع الشبكة بدل الاعتماد على `queue_on_failure=True` المتناثر داخل `RestClient` فقط.

هذه المرحلة لا تجعل كل النظام يعمل Offline. بالعكس: تميّز صراحة بين:

- عمليات آمنة للصفّ وإعادة الإرسال لاحقًا.
- عمليات يجب منعها عند انقطاع الشبكة لأنها تحتاج حالة سيرفر/فرع/وردية مباشرة.
- تقارير وقراءات لا تُصف كطلبات كتابة.
- طباعة/تصدير يمكن تنفيذها محليًا إذا كانت البيانات محمّلة مسبقًا.

## الملفات الجديدة

- `alrajhi_client/workspace/sync/offline_sync_contract.py`
- `alrajhi_client/workspace/sync/__init__.py`
- `tools/offline_sync_contract_audit.py`
- `tests/test_phase265_offline_queue_sync_contract_audit.py`

## أهم القرارات

### Queueable writes
العمليات التالية قابلة للصف عند فشل الاتصال:

- فواتير البيع والشراء عبر `/api/invoices`
- مرتجعات البيع عبر `/api/returns/sales`
- مرتجعات الشراء عبر `/api/returns/purchase`
- المواد عبر `/api/items`
- العملاء عبر `/api/customers`
- الموردون عبر `/api/suppliers`
- السندات عبر `/api/vouchers`
- المصروفات عبر `/api/expenses`
- أحداث التدقيق عبر `/api/audit_log`

### Online-only / blocked
العمليات التالية لا تُصف تلقائيًا لأنها تحتاج اتساقًا مباشرًا:

- الورديات والصناديق.
- عمليات المطعم والجلسات والطاولات والمطبخ.
- المستودعات والتحويلات والمخزون الحي.
- الفروع والمستخدمون والصلاحيات والإعدادات.
- التقارير كقراءات من السيرفر.

### POS
`POS checkout` يمكن صفّه فقط لأنه يتحول إلى فاتورة بيع عبر `/api/invoices`. أما فتح/إغلاق الوردية وحالة الصندوق فتبقى online-only.

### Audit
تمت إضافة `/api/audit_log` إلى قائمة queueable prefixes حتى لا تختفي أحداث التدقيق عند انقطاع السيرفر.

## تحديث Offline Queue
تمت إضافة metadata إلى جدول queue:

- `payload_hash`
- `idempotency_key`
- `sync_scope`
- `conflict_policy`
- `replay_priority`
- `branch_id`

كما أصبح ترتيب replay يعتمد على `replay_priority` ثم `id`.

## الفحص

```bash
python tools/offline_sync_contract_audit.py
```

ينتج:

`tools/audit_outputs/offline_sync_contract_matrix.csv`

## حدود المرحلة
هذه المرحلة تؤسس عقد sync وتربطه بالـ queue. لا تنفذ بعد conflict resolver تفاعلي أو شاشة مراجعة تعارضات. هذا مناسب لمرحلة لاحقة.
