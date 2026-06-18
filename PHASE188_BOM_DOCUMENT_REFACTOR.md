# Phase 188 — BOM Document Refactor

## الهدف
تحويل محرر تركيبة التصنيع BOM من تبويب يغلف `BOMDialog` القديم إلى تبويب تصنيع حقيقي داخل نظام التبويبات، مع الحفاظ على `BOMDialog` كـ legacy fallback فقط.

## ما تم تنفيذه

- استبدال `BomDocumentTab(DialogDocumentTab)` بـ `BomDocumentTab(BaseDocumentTab)`.
- إبقاء `LegacyBomDocumentTab` كجسر fallback صريح حول `BOMDialog` القديم.
- إنشاء Grid احترافي للمواد الداخلة في التركيبة:
  - `features/manufacturing/grids/bom_components_grid.py`
  - `features/manufacturing/grids/bom_components_model.py`
  - `features/manufacturing/grids/manufacturing_column_schema.py`
- إعادة استخدام `TransactionLineGrid` بدل `QListWidget` القديم.
- إعادة استخدام `TransactionItemDelegate` و`TransactionUnitDelegate` عبر contract:
  - `set_item()`
  - `set_unit()`
  - `unit_options_for_row()`
- دعم البحث اليدوي عن المادة داخل BOM عبر `barcode_input_service.lookup_entry()`.
- دعم باركود المادة وباركود الوحدة في إدخال مكونات BOM.
- دعم `unit_id`, `conversion_factor`, `base_qty`, `unit_cost`, `total_cost` داخل نموذج المكونات.
- إضافة panel مستقل لملخص تكلفة التركيبة:
  - تكلفة المواد
  - تكلفة الهدر
  - الكمية الأساسية المطلوبة
  - تكلفة وحدة المنتج النهائي
  - عدد المكونات
- ربط الحفظ بـ `manufacturing_service.save_bom()` فقط، دون DAO مباشر.
- احترام صلاحيات Phase 187:
  - `OP_BOM_CREATE`
  - `OP_BOM_EDIT`
  - `OP_PRINT`
- إضافة ترجمات عربية/ألمانية/إنجليزية لمفاتيح BOM الجديدة.

## الفحوص

تم تشغيل:

```bash
python tools/phase184_case_insensitive_material_lookup_guard.py
python tools/phase185_invoice_grid_item_lookup_guard.py
python tools/phase186_pos_returns_lookup_audit_guard.py
python tools/phase187_manufacturing_governance_guard.py
python tools/phase188_bom_document_refactor_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

## ملاحظات

- لم يتم بعد بناء جسر طباعة التصنيع. زر الطباعة محفوظ ومربوط بالصلاحية، لكنه يعرض رسالة مرحلية إلى حين Phase تصنيع الطباعة.
- لم يتم بعد تحويل أمر الإنتاج أو تفاصيل أمر الإنتاج. هذا سيكون في Phase 189 وPhase 190.
