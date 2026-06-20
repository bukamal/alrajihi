# Phase 279 — Phase 32 Offline Queue Guard Hotfix

## الهدف

إصلاح فشل CI في:

```bash
python tools/phase32_invoice_flow_guard.py
```

والرسالة:

```text
Offline queue must permanently fail validation/auth/not-found/conflict 4xx responses
```

## سبب الفشل

منطق Phase 270 كان صحيحًا وظيفيًا: أخطاء 400/401/403/404/422 تتحول إلى `failed`، و409 يتحول إلى `conflict` نهائي للمراجعة اليدوية بدل إعادة المحاولة اللانهائية.

لكن حارس Phase 32 قديم ويبحث نصيًا داخل `offline_queue_gateway.py` عن قائمة أكواد 4xx النهائية:

`400, 401, 403, 404, 409, 422`

بعد نقل التصنيف إلى `workspace.sync.replay_safety` لم تعد القائمة الحرفية موجودة داخل ملف gateway نفسه، ففشل الحارس رغم أن السلوك النهائي موجود.

## التعديل

أضيف ثابت توافق داخل:

`alrajhi_client/gateways/local/offline_queue_gateway.py`

```python
TERMINAL_REPLAY_4XX_STATUS_CODES = (400, 401, 403, 404, 409, 422)
```

مع تعليق يوضح أن:

- 400/401/403/404/422 تفشل نهائيًا عبر `offline_queue.mark_failed`.
- 409 حالة نهائية أيضًا لكنها تذهب إلى `conflict/manual review` عبر `offline_queue.mark_conflict`، ولا تُعاد محاولتها بلا نهاية.

## التحقق

- `python tools/phase32_invoice_flow_guard.py` يمر الآن.
- تمت إضافة اختبار يثبت أن حارس Phase 32 لا يعود للفشل.
