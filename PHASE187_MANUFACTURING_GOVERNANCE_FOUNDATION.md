# Phase 187 — Manufacturing Governance Foundation

## الهدف

تثبيت طبقة حوكمة موحدة للتصنيع قبل إعادة بناء واجهات BOM وأوامر الإنتاج بصريًا.

## ما تم

- إضافة `settings_service.get_manufacturing_settings()` كعقد إعدادات موحد للتصنيع.
- إضافة `manufacturing_operation_policy` للتحكم بعمليات التصنيع الحساسة عبر الإعدادات، الصلاحيات، RBAC، والتدقيق.
- ربط `ManufacturingService` بالـ operation policy حتى لا يمكن تجاوز الواجهة واستدعاء الخدمة مباشرة لتنفيذ عمليات تصنيع غير مصرح بها.
- إضافة صلاحيات تصنيع مستقلة إلى `permission_service` و`rbac_service`.
- إضافة permissions/migrations للعميل والخادم.
- إضافة مفاتيح ترجمة لعمليات التصنيع بالعربية والألمانية والإنجليزية.
- إضافة guard يمنع تجاوز طبقة المشروع داخل `features/manufacturing`.

## العمليات المحكومة

- استخدام التصنيع.
- إنشاء/تعديل/حذف BOM.
- إنشاء/بدء/إلغاء/حذف/عكس أمر إنتاج.
- استهلاك مواد الإنتاج.
- إتمام مخرجات الإنتاج.
- حذف الاستهلاك والمخرجات.
- عرض تكلفة التصنيع.
- طباعة مستندات التصنيع.

## الفحوص

تم تشغيل:

```text
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase184_case_insensitive_material_lookup_guard.py
python tools/phase185_invoice_grid_item_lookup_guard.py
python tools/phase186_pos_returns_lookup_audit_guard.py
python tools/phase187_manufacturing_governance_guard.py
```

كما تم تشغيل guards المراحل 169 إلى 183 على دفعات؛ بعض التشغيل الجماعي الطويل قد يتأثر بمهلة البيئة، لكن guards الأخيرة نجحت منفردة.

## ما لم يتم بعد

لم يتم تحويل `BOMDialog` و`ProductionOrderDialog` و`ProductionDetailsDialog` بصريًا إلى مستندات جديدة. بقيت legacy fallback مؤقتًا.

المرحلة التالية المنطقية:

```text
Phase 188 — BOM Document Refactor
```

وتشمل بناء BOM tab مستقل مع grid للمواد الداخلة، item/unit delegates، دعم باركود الوحدة، وملخص تكلفة.
