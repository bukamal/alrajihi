# Phase 102 — اختبار حسابي فعلي لنظام المرتجعات

## نطاق الاختبار
تم تشغيل قاعدة SQLite فعلية من الصفر واستخدام مسارات التطبيق المحلية:
- `invoice_service.create`
- `LocalSalesReturnGateway.create_return/delete_return`
- `LocalPurchaseReturnGateway.create_return/delete_return`
- `warehouse_service.record_movement`

تم فحص الجداول:
`items`, `item_warehouse_balances`, `inventory_movements`, `warehouse_movements`, `inventory_ledger`, `sales_returns`, `sales_return_lines`, `purchase_returns`, `purchase_return_lines`, `customers`, `suppliers`, `users`, `cash_bank_movements`.

## أخطاء ظهرت قبل الإصلاح
1. إلغاء مرتجع الشراء المحلي كان يعيد رصيد المستودع، لكنه لا يعيد حساب `items.quantity` بعد حذف حركة `purchase_return` من `inventory_movements`.
2. مرتجع البيع كان يعيد المخزون بتكلفة مساوية لسعر البيع عند وجود `invoice_lines.unit_cost` قديم/موروث، بدل تكلفة البضاعة المباعة COGS المستخرجة من `invoice_lines.cost_amount / quantity_in_base`.

## الإصلاحات المنفذة
- `alrajhi_client/gateways/local/purchase_return_gateway.py`: إضافة تحديث `items.quantity` وإعادة حساب `average_cost` بعد حذف حركة مرتجع الشراء.
- `alrajhi_client/gateways/local/sales_return_gateway.py`: حساب تكلفة مرتجع البيع من `cost_amount / quantity_in_base` عند توفرها.
- `alrajhi_server/api/returns.py`: توحيد نفس قاعدة تكلفة مرتجع البيع في مسار الخادم.

## سيناريو بيع آجل جزئي
افتتاحي: كمية 10، تكلفة 50، سعر بيع 100.
فاتورة بيع: 4 × 100، مدفوع 150، ذمة 250.
مرتجع بيع: 2 × 100، كامل المرتجع يخصم من ذمة العميل لأن الذمة المتبقية 250.

النتيجة بعد المرتجع:
- `items.quantity = 8`
- رصيد المستودع = 8
- رصيد العميل = 50
- نقدية المستخدم = 1150
- `sales_returns.total = 200`, `refund_amount = 0`, `credit_amount = 200`
- تكلفة حركة `sales_return` = 50 وليس 100

بعد إلغاء المرتجع:
- `items.quantity = 6`
- رصيد المستودع = 6
- رصيد العميل = 250
- النقدية بقيت 1150

## سيناريو شراء آجل جزئي
بعد إلغاء مرتجع البيع: الكمية 6.
فاتورة شراء: 5 × 60، مدفوع 120، ذمة مورد 180.
مرتجع شراء: 2 × 60، كامل المرتجع يخصم من ذمة المورد.

النتيجة بعد المرتجع:
- `items.quantity = 9`
- رصيد المستودع = 9
- رصيد المورد = 60
- نقدية المستخدم = 1030
- `purchase_returns.total = 120`, `refund_amount = 0`, `credit_amount = 120`

بعد إلغاء مرتجع الشراء:
- `items.quantity = 11`
- رصيد المستودع = 11
- رصيد المورد = 180
- النقدية بقيت 1030

## سيناريو رد نقدي كامل — بيع
فاتورة بيع نقدية كاملة: 3 × 80، مدفوع 240.
مرتجع بيع: 2 × 80.

النتيجة:
- `refund_amount = 160`
- `credit_amount = 0`
- حركة `cash_bank_movements`: `sales_return_refund`, مبلغ `-160`, اتجاه `out`
- بعد إلغاء المرتجع تُحذف حركة الصندوق ويعود النقد إلى حالة ما بعد الفاتورة.

## سيناريو استرداد نقدي كامل — شراء
فاتورة شراء نقدية كاملة: 3 × 40، مدفوع 120.
مرتجع شراء: 2 × 40.

النتيجة:
- `refund_amount = 80`
- `credit_amount = 0`
- حركة `cash_bank_movements`: `purchase_return_refund`, مبلغ `80`, اتجاه `in`
- بعد إلغاء المرتجع تُحذف حركة الصندوق ويعود النقد إلى حالة ما بعد الفاتورة.

## اختبار منع الإرجاع الزائد
محاولة إرجاع 999 من بند شراء كميته الأصلية 5 أعطت الخطأ المتوقع:
`كمية المرتجع أكبر من الكمية المتبقية القابلة للإرجاع`

## حكم الاختبار
بعد الإصلاحات، مسارات المرتجعات المحلية والخادمية المعدّلة متسقة في:
- الكمية العامة `items.quantity`
- رصيد المستودع `item_warehouse_balances`
- حركات `inventory_movements`
- حركات `warehouse_movements`
- أرصدة العملاء والموردين
- النقدية العامة وحركات الصندوق/البنك عند وجود refund
- سعر البيع وسعر الشراء الأساسي لا يتغيران بعد الإرجاع
- تكلفة مرتجع البيع تُسجل بتكلفة البضاعة لا بسعر البيع
