# Phase 184 — Case-Insensitive Material Lookup

## الهدف
تأكيد وتصحيح أن حقل البحث عن المادة في فواتير البيع والشراء لا يتأثر بحالة الأحرف عند البحث اليدوي، مع إبقاء قراءة الباركود exact حتى لا يتم إدخال مادة خاطئة.

## ما تم

- تعديل البحث المحلي في `DatabaseConnection.get_items()` ليستخدم:
  - `LOWER(COALESCE(name,'')) LIKE LOWER(?)`
  - `LOWER(COALESCE(barcode,'')) LIKE LOWER(?)`

- تعديل endpoint الخادم `GET /api/items` بنفس المنطق حتى يكون سلوك local و API موحدًا.

- تحسين `BarcodeInputService.lookup_manual()`:
  - البحث اليدوي أصبح يجلب حتى 10 نتائج بدل 2 فقط.
  - إذا كانت النتائج متعددة، يتم تفضيل التطابق الكامل لاسم المادة باستخدام `casefold()`.
  - قراءة الباركود بقيت exact ولا تتحول إلى بحث نصي.

- إضافة completer لحقل البحث السريع في `TransactionDocumentTab`:
  - `Qt.CaseInsensitive`
  - `Qt.MatchContains`
  - تحديث ديناميكي من `catalog_service.items()`
  - تعطيل الاقتراحات عند إدخال نص يبدو كقراءة scanner حتى لا نخلط scan بالبحث اليدوي.

## لماذا لم نجعل الباركود exact case-insensitive؟
باركود `CODE128` قد يكون حساسًا لحالة الأحرف، لذلك مسار scanner بقي exact عمدًا. التعديل يخص البحث اليدوي عن اسم المادة/النص فقط.

## الفحص
أضيف guard:

```text
tools/phase184_case_insensitive_material_lookup_guard.py
```

ويفحص:

- وجود predicates غير حساسة لحالة الأحرف في local/server item search.
- وجود disambiguation بـ `casefold()` داخل `BarcodeInputService`.
- وجود `QCompleter` غير حساس لحالة الأحرف في `TransactionDocumentTab`.
- اختبار SQLite فعلي مع `PRAGMA case_sensitive_like=ON` لإثبات أن predicate الجديد يعمل حتى لو صار `LIKE` حساسًا.
