# Gateway Phase 31 - Inventory Ledger Dual Read

## الهدف
إضافة وضع قراءة مزدوجة للمخزون دون تغيير المصدر التشغيلي الحالي.

## المضاف
- `InventoryLedgerDAO.dual_read_report()`
- `InventoryService.ledger_dual_read()`
- `InventoryGateway.ledger_dual_read()`
- `RestClient.get_inventory_ledger_dual_read()`
- `GET /api/inventory-ledger/dual-read`

## السلوك
- الرصيد التشغيلي القديم يبقى المصدر المعتمد.
- Ledger يُقرأ للمقارنة فقط.
- يعرض الفرق لكل صنف ومستودع.
- لا يغيّر أي كمية أو حركة.

## نتيجة المرحلة
النظام أصبح قادراً على اختبار جاهزية التحول إلى Ledger Authoritative Mode لاحقاً، مع بقاء التشغيل الحالي آمناً.
