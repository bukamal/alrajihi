# Phase 53 — Manufacturing Details Hotfix

## الهدف
إصلاح أخطاء واجهة التصنيع التي ظهرت أثناء إنشاء أمر إنتاج وعرض تفاصيله.

## المشاكل التي تم إصلاحها

1. جدول أمر الإنتاج كان يعرض عمود المادة فارغاً في بعض الحالات، خصوصاً عند استخدام REST API.
2. تفاصيل أمر الإنتاج كانت قد تظهر ناقصة أو فارغة لأن Endpoint تفاصيل الأمر لم يكن يرجع أسماء المنتج/المواد/المستودعات بشكل كامل.
3. تحذير Qt:
   `QLayout: Attempting to add QLayout ... ProductionDetailsDialog ... already has a layout`
   بسبب وضع `QVBoxLayout(self)` داخل Dialog مبني على `CenteredDialog`، بينما يجب استخدام `self.content_widget`.
4. إصلاح خطأ كامن في `ManufacturingService.check_materials_availability` حيث كان يستخدم متغيراً غير معرف `order_id` بدلاً من تمرير `*args`.

## التعديلات

- `ProductionDetailsDialog` يستخدم الآن:
  `QVBoxLayout(self.content_widget)`
- إضافة fallback لعرض اسم المادة:
  `مادة #id` عند غياب الاسم من API.
- تحسين `ProductionOrderDialog` لعدم ترك عمود المادة فارغاً حتى إذا رجع API بدون `item_name`.
- تحسين `alrajhi_server/api/manufacturing.py` لإرجاع:
  - `item_name` في BOM lines.
  - `product_name` في تفاصيل أمر الإنتاج.
  - `raw_warehouse_name` و `output_warehouse_name`.
  - أسماء المواد في reservations / consumptions / outputs.
- إضافة فحص:
  `tools/manufacturing_ui_guard.py`

## الفحوصات

- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
- offline_read_guard: PASS
- offline_widget_guard: PASS
- form_validation_guard: PASS
- manufacturing_ui_guard: PASS
- zip test: PASS
