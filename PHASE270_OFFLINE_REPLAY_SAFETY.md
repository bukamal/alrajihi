# PHASE270 — Offline Conflict Resolution / Replay Safety

## الهدف

استئناف المتابعة العامة بعد إصلاحات الطباعة والواجهات الموضعية، والانتقال من مجرد تحديد ما يمكن صفّه عند انقطاع الشبكة إلى ضبط إعادة الإرسال نفسها: منع التكرار، إرسال مفاتيح idempotency، تصنيف أخطاء replay، وعزل التعارضات للمراجعة اليدوية بدل إعادة المحاولة بلا نهاية.

## ما تم

### 1. عقد أمان إعادة الإرسال

أُضيف الملف:

`alrajhi_client/workspace/sync/replay_safety.py`

ويغطي:

- بناء `idempotency_key` مستقر من مرجع المستند أو `record_id` أو `payload_hash`.
- إرسال headers أثناء replay:
  - `Idempotency-Key`
  - `X-Idempotency-Key`
  - `X-Alrajhi-Offline-Replay`
  - `X-Alrajhi-Sync-Scope`
  - `X-Alrajhi-Conflict-Policy`
  - `X-Alrajhi-Branch-Id`
- تصنيف أخطاء API:
  - `409` → conflict/manual review.
  - `400/401/403/404/422` → failed نهائيًا.
  - أخطاء الاتصال و `429/5xx` → retry.

### 2. منع تكرار الطلبات المعلقة

تم تعديل:

`alrajhi_client/database/connection.py`

بحيث لا يضيف الطابور طلبًا جديدًا إذا كان هناك طلب pending بنفس `idempotency_key` لنفس الجلسة. هذا يمنع تكرار نفس فاتورة/مرتجع/سند عند الضغط المتكرر أو تكرار فشل الاتصال.

### 3. توسيع metadata الطابور

تمت إضافة أعمدة آمنة متوافقة مع قواعد قديمة:

- `replay_locked_at`
- `replay_error_category`
- `manual_review_reason`

مع فهرس:

`idx_offline_queue_idempotency`

### 4. replay headers داخل RestClient

تم تعديل:

`alrajhi_client/database/connection_rest.py`

ليدعم `extra_headers` في `_request()`، ويستخدمها أثناء إعادة إرسال الطلبات من الطابور.

### 5. تصنيف التعارضات داخل OfflineQueueGateway

تم تعديل:

`alrajhi_client/gateways/local/offline_queue_gateway.py`

بحيث:

- يقفل الطلب مؤقتًا أثناء replay.
- يرسل headers الخاصة بالـ idempotency/sync.
- يضع طلبات `409` في حالة `conflict` بدل `failed` أو إعادة محاولة لا نهائية.
- يضع أخطاء validation/auth/not-found في `failed` نهائيًا.
- يعيد المحاولة فقط للأخطاء القابلة للإعادة.

### 6. أداة فحص

أُضيفت:

`tools/offline_replay_safety_audit.py`

وتكتب:

`tools/audit_outputs/offline_replay_safety_matrix.csv`

## الاختبارات

أُضيف:

`tests/test_phase270_offline_replay_safety.py`

نتائج الفحص:

- `compileall`: ناجح.
- `pytest`: `243 passed`, `1 warning`.

## ملاحظات معمارية

هذه المرحلة لا تجعل كل عملية offline-safe. بل تجعل العمليات التي سبق التصريح بأنها queueable في Phase 265 أكثر أمانًا عند replay. عمليات مثل الورديات، الصناديق، المطعم، الجلسات، والتحويلات الحساسة تبقى online-only حسب العقد السابق.
