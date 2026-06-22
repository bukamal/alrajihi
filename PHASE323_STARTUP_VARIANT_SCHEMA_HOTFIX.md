# Phase 323 — Startup Variant Schema Hotfix

## الهدف
إصلاح فشل بدء التشغيل على قواعد بيانات قديمة أنشأت جدول `warehouse_movements` قبل إضافة أعمدة متغيرات الألبسة.

## المشكلة
كان `apply_common_schema` ينشئ فهرس `idx_wh_mov_variant` على `warehouse_movements(variant_id)` من داخل مجموعة فهارس `item_variants`، وبالتالي قد يتم تنفيذ الفهرس قبل ضمان وجود عمود `variant_id` في جدول `warehouse_movements`.

الخطأ الناتج:

```text
sqlite3.OperationalError: no such column: variant_id
```

## الإصلاح
- إضافة أعمدة متغيرات الألبسة إلى `REQUIRED_COLUMNS` لكل من العميل والخادم.
- فصل فهارس `warehouse_movements` عن فهارس `item_variants`.
- فصل فهارس `item_warehouse_variant_balances` في مجموعة مستقلة.
- ضمان ترقية الجداول القديمة قبل إنشاء الفهارس.

## النطاق المحفوظ
- لا تغيير في API.
- لا تغيير في الواجهات.
- لا تغيير في الطباعة الموحدة.
- لا تغيير في تعدد المستخدمين أو RTL/LTR أو اللغات.
- لا تغيير في محرك الألبسة نفسه؛ الإصلاح خاص بترقية قاعدة البيانات عند بدء التشغيل.

## التحقق
- اختبار Legacy database client/server يثبت أن الأعمدة تضاف قبل الفهرس.
- الحراس العامة تمر بعد الإصلاح.
