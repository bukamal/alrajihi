# GATEWAY PHASE 25 REPORT

## الهدف
توسيع Inventory Ledger بنمط Shadow Posting ليشمل الحركات المستودعية والتحويلات، دون تغيير الرصيد التشغيلي الحالي أو اعتماد ledger كمصدر نهائي.

## التغييرات

### Server
- تعديل `alrajhi_server/api/warehouses.py`.
- إضافة helper:
  - `_post_inventory_ledger_entry(...)`
  - `_ledger_direction_from_qty(...)`
- ربط:
  - `POST /api/warehouses/movements` → ledger shadow entry للحركات المباشرة.
  - `POST /api/warehouses/transfers` → ledger out من المستودع المصدر و ledger in إلى المستودع الوجهة.
  - `POST /api/warehouses/transfers/<id>/cancel` → ledger reversal لإلغاء التحويل.

### Client Local
- تعديل `alrajhi_client/core/services/warehouse_service.py`.
- في الوضع المحلي فقط:
  - `record_movement(...)` يسجل ledger موازٍ للحركات المستودعية المباشرة.
  - `create_transfer(...)` يسجل ledger out/in للتحويل.
  - `cancel_transfer(...)` يسجل reversal للتحويل.
- في الوضع Remote لا يسجل العميل ledger للتحويلات؛ الخادم هو المسؤول، منعاً للتكرار.

## الحماية من التكرار
تم استثناء reference types الآتية من ledger العام للحركات المستودعية لأنها لها hooks مخصصة:
- `invoice`
- `sales_return`
- `purchase_return`

## الفحوصات
- `python3 -m compileall -q alrajhi_client alrajhi_server`: ناجح.
- `python3 tools/architecture_guard.py`: ناجح.
- لا توجد استثناءات `DatabaseConnection` قديمة داخل الطبقات المحمية.

## ملاحظة تشغيلية
هذا لا يغير حساب الرصيد الحالي. الرصيد التشغيلي ما زال من الجداول الحالية، والـ `inventory_ledger` ما زال سجل تدقيق/مقارنة موازياً.
