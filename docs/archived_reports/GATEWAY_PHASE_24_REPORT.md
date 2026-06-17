# Gateway Phase 24 Report

## الهدف
توسيع Inventory Ledger shadow-posting ليشمل المرتجعات دون تغيير منطق المخزون الحالي أو جعل Ledger مصدر الرصيد النهائي.

## التعديلات

### Server
- تعديل `alrajhi_server/api/returns.py`.
- إضافة helper functions:
  - `_post_return_ledger_entry`
  - `_post_return_ledger_entries`
  - `_post_return_ledger_reversal`
- عند إنشاء مرتجع بيع:
  - يسجل Ledger entry بنوع `sales_return_in` واتجاه `in`.
- عند إنشاء مرتجع شراء:
  - يسجل Ledger entry بنوع `purchase_return_out` واتجاه `out`.
- عند حذف/إلغاء مرتجع بيع:
  - يسجل reversal بنوع `sales_return_reversal` واتجاه `out`.
- عند حذف/إلغاء مرتجع شراء:
  - يسجل reversal بنوع `purchase_return_reversal` واتجاه `in`.

### Client Local
- تعديل `alrajhi_client/gateways/local/sales_return_gateway.py`.
- تعديل `alrajhi_client/gateways/local/purchase_return_gateway.py`.
- إضافة shadow ledger محلي عند إنشاء/إلغاء المرتجعات.

## حدود المرحلة
- لا يوجد اعتماد على Ledger لحساب الرصيد.
- لا يوجد حذف فعلي من Ledger.
- لا يوجد تعديل على `inventory_movements` الحالي.
- لا يوجد تغيير في أثر المرتجعات على المخزون الحالي.

## الفحوصات
- `python3 -m compileall -q alrajhi_client alrajhi_server` ✅
- `python3 tools/architecture_guard.py` ✅
- AST/static smoke checks للـ return ledger hooks ✅
- ZIP integrity ✅

## الاختبار المقترح
1. إنشاء فاتورة شراء.
2. إنشاء مرتجع شراء جزئي.
3. مراجعة `/api/inventory-ledger?reference_type=purchase_return`.
4. إنشاء فاتورة بيع.
5. إنشاء مرتجع بيع جزئي.
6. مراجعة `/api/inventory-ledger?reference_type=sales_return`.
7. حذف/إلغاء المرتجع والتأكد من إضافة reversal بدل حذف السجل.
