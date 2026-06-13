# Gateway Phase 29 Report

## الهدف
توسيع Backfill الخاص بـ `Inventory Ledger` ليغطي الحركات المستودعية القديمة على مستوى المستودع، مع إبقاء التشغيل الحالي كما هو.

## التغييرات
- إضافة `InventoryLedgerDAO.backfill_from_warehouse_movements(...)`.
- إضافة `InventoryLedgerDAO.backfill_ledger(...)` كمنسق شامل للتعبئة.
- تحديث `InventoryGateway.ledger_backfill(...)` لدعم:
  - `warehouse_id`
  - `include_item_movements`
  - `include_warehouse_movements`
- تحديث `LocalInventoryGateway` و `RemoteInventoryGateway`.
- تحديث `RestClient.inventory_ledger_backfill(...)`.
- تحديث endpoint:
  - `POST /api/inventory-ledger/backfill`

## السلوك
- `dry_run=True` افتراضياً.
- لا يتم تعديل `items.quantity`.
- لا يتم تعديل `item_warehouse_balances`.
- يتم تجنب التكرار عبر `source_table + source_id`.
- التحويلات المستودعية مغطاة من خلال صفوف `warehouse_movements` (`transfer_out` / `transfer_in`) لتجنب double posting من `warehouse_transfers`.

## الفحوصات
- `compileall`: ناجح.
- `architecture_guard`: ناجح.
- AST syntax check: ناجح.
- Gateway method coverage check: ناجح.

## ملاحظة
هذه المرحلة ما زالت Shadow Ledger فقط، وليست تحويل الرصيد التشغيلي للاعتماد على Ledger.
