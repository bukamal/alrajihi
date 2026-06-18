# Phase 172 — Material Unit Barcode API

## الهدف

توحيد باركود المادة وباركود الوحدة داخل نفس مسار الباركود الدقيق، حتى تعمل الفواتير والمرتجعات وPOS لاحقًا بنفس السلوك:

- باركود المادة الأساسية يفتح المادة بالوحدة الأساسية.
- باركود وحدة فرعية يفتح نفس المادة مع `matched_unit` ومعامل التحويل الصحيح.
- لا يوجد fallback إلى أول نتيجة بحث.
- التخزين المحلي والـ API يحفظان باركود الوحدة والملاحظات.

## التغييرات الرئيسية

### قاعدة البيانات

تم توسيع `item_units` في العميل والخادم:

```sql
barcode TEXT
notes TEXT
```

وتمت إضافة ترقيات idempotent داخل `schema_manager` للعميل والخادم، مع فهارس:

```sql
idx_item_units_item
idx_item_units_barcode
```

### التخزين المحلي

تم تعديل:

```text
alrajhi_client/database/repositories/item_repo.py
alrajhi_client/database/dao/item_dao.py
alrajhi_client/database/connection.py
```

ليدعم:

- قراءة `barcode` و`notes` للوحدات.
- حفظ `barcode` و`notes` للوحدات.
- البحث الدقيق عن باركود الوحدة عبر `get_item_by_barcode()`.
- إرجاع `matched_unit` و`barcode_scope` عند مطابقة باركود وحدة.

### API

تم تعديل:

```text
alrajhi_server/repositories/http_route_sql/items.py
```

ليدعم:

- حفظ باركود الوحدة داخل POST/PUT `/api/items`.
- إرجاع الوحدات مع `barcode` و`notes`.
- البحث في `/api/items/by-barcode` داخل `items.barcode` و`item_units.barcode`.
- إرجاع `matched_unit` عند مطابقة باركود وحدة.
- التحقق من عدم تكرار الباركود بين المادة الأساسية والوحدات.

### Product Service

تم تعديل:

```text
alrajhi_client/core/services/product_service.py
```

ليدعم:

- تطبيع باركود الوحدة عبر `barcode_service`.
- التحقق من تكرار باركود الوحدة.
- منع تكرار الباركود بين المادة ووحداتها.
- حفظ باركود وملاحظات الوحدة عبر `replace_units()`.

### Transaction Line Grid

تم تعديل:

```text
alrajhi_client/features/transactions/grids/transaction_line_model.py
```

ليدعم:

- قراءة `matched_unit` من نتيجة الباركود.
- اختيار `unit_id` و`unit` و`conversion_factor` تلقائيًا.
- تسعير الوحدة الفرعية بضرب سعر الوحدة الأساسية في معامل التحويل عند عدم وجود سعر وحدة صريح.

## مثال سلوك

مادة: ماء

```text
الوحدة الأساسية: قطعة
سعر القطعة: 1
وحدة فرعية: كرتون
معامل التحويل: 24
باركود الكرتون: 1234567890128
```

عند قراءة باركود الكرتون في فاتورة البيع:

```text
item_id = ماء
unit = كرتون
conversion_factor = 24
price = 24
qty = 1
quantity_in_base = 24 لاحقًا عند الحفظ
```

## الفحوص

تمت إضافة:

```text
tools/phase172_unit_barcode_api_guard.py
```

وتم تشغيل:

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
python tools/phase171_material_document_guard.py
python tools/phase172_unit_barcode_api_guard.py
```

كلها نجحت.

## ملاحظة تنفيذية

هذه المرحلة لا تنشئ POS بعد. لكنها تجعل POS لاحقًا قادرًا على قراءة باركود الكرتون/الصندوق/العلبة بنفس محرك الباركود المستخدم في الفواتير والمواد.
