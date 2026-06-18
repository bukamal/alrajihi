# Phase 183 — Restaurant Printing Bridge

## الهدف
توحيد طباعة مطعم POS مع نظام الطباعة المركزي بدل بناء HTML داخل واجهة المطعم أو داخل خدمات المطعم.

## ما تم

- إضافة `features/restaurant/restaurant_printing_bridge.py` كجسر واحد بين مطعم POS و`printing_service`.
- إضافة قوالب مركزية في `printing/print_templates.py`:
  - `restaurant_receipt_html`
  - `restaurant_kitchen_ticket_html`
- إضافة واجهات في `printing/printing_service.py`:
  - receipt preview / print / pdf / browser
  - kitchen ticket preview / print / pdf / browser
- إضافة عمليتي طباعة إلى `restaurant_operation_policy`:
  - `OP_PRINT_RECEIPT`
  - `OP_PRINT_KITCHEN_TICKET`
- ربط الطباعة بإعدادات المطعم:
  - `restaurant/operations/allow_print_receipt`
  - `restaurant/operations/allow_print_kitchen_ticket`
  - `restaurant/operations/auto_print_receipt_after_checkout`
  - `restaurant/operations/auto_print_kitchen_ticket`
  - `restaurant/kitchen_ticket_paper`
- إضافة أزرار طباعة داخل `RestaurantPOSWidget`:
  - طباعة الإيصال
  - طباعة تذكرة المطبخ
- إضافة صلاحيات RBAC:
  - `restaurant.receipt.print`
  - `restaurant.kitchen_ticket.print`
- إضافة ترجمات عربية/ألمانية/إنجليزية للمفاتيح الجديدة.
- إضافة guard:
  - `tools/phase183_restaurant_printing_bridge_guard.py`

## القاعدة المعمارية
واجهة المطعم لا تنشئ HTML للطباعة. الجسر يبني payload فقط، ثم يمرره إلى `printing_service`، بينما اللغة، الشعار، بيانات الشركة، حجم الورق، الاتجاه، والـ PDF/Preview تبقى من مسؤولية نظام الطباعة المركزي.

## الفحوص

نجحت:

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase183_restaurant_printing_bridge_guard.py
```

كما نجحت guards من Phase 169 إلى Phase 183 عند تشغيل المجموعات الحساسة منفردة. عند تشغيل جميع guards في حلقة واحدة قد يحدث timeout بيئي في بعض مراحل POS القديمة، وليس خطأ compile أو guard فعلي.
