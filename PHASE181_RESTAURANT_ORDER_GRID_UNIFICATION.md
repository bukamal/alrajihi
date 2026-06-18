# Phase 181 — Restaurant Order Grid Unification

## الهدف
نقل قائمة طلبات المطعم من `QListWidget` القديم إلى جدول Model/Grid موحد يدعم اللمس، أعمدة الوحدات، كمية الأساس، ونوع الباركود، مع الحفاظ على workflow المطعم الحالي.

## ما تم

- إنشاء حزمة `features/restaurant`.
- إضافة `RestaurantOrderGrid` مبني فوق `TransactionLineGrid`.
- إضافة `RestaurantOrderModel` مبني فوق `QAbstractTableModel`.
- إضافة `restaurant_order_schema` لأعمدة طلب المطعم.
- استبدال `QListWidget` داخل `restaurant_pos_widget.py` بـ `RestaurantOrderGrid`.
- ربط تحميل سطور الجلسة عبر `order_model.set_lines()`.
- إضافة أعمدة مهمة:
  - المادة
  - الإضافات
  - الوحدة
  - الكمية
  - الكمية الأساسية
  - السعر
  - الإجمالي
  - حالة المطبخ
  - نوع الباركود
  - الملاحظات
- الحفاظ على دعم Phase 180:
  - باركود المادة
  - باركود الوحدة
  - `unit_id`
  - `conversion_factor`
  - `base_qty`
  - `barcode_scope`
  - `matched_barcode`

## ما لم يتم بعد

- لم يتم بناء Payment Shell كامل للمطعم.
- لم يتم إضافة تعديل/حذف مباشر داخل grid.
- لم يتم نقل إدارة الطاولات كلها إلى grids حديثة.
- لم يتم تطبيق صلاحيات عمليات المطعم بنفس عمق POS العادي.

## الفحص

تم تشغيل:

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
python tools/phase171_material_document_guard.py
python tools/phase172_unit_barcode_api_guard.py
python tools/phase173_material_workspace_guard.py
python tools/phase174_material_security_guard.py
python tools/phase175_pos_touch_guard.py
python tools/phase176_pos_visual_grid_guard.py
python tools/phase177_pos_payment_shell_guard.py
python tools/phase178_pos_operation_governance_guard.py
python tools/phase179_pos_shift_disabled_guard.py
python tools/phase180_restaurant_barcode_unit_guard.py
python tools/phase181_restaurant_order_grid_guard.py
```

كل الفحوص نجحت.
