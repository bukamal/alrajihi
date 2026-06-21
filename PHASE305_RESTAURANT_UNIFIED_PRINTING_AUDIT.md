# Phase 305 — Restaurant Unified Printing Audit

## الهدف

تثبيت أن طباعة المطعم ليست مسارًا مستقلًا عن نظام الطباعة الموحد، بل تستخدم نفس سطح Browser HTML المركزي مع قوالب مطعم خاصة.

## النطاق

- إيصال العميل: `restaurant_receipt`.
- تذكرة المطبخ/KOT: `restaurant_kitchen`.
- ملخص الجلسة/الطاولة: `restaurant_session_summary`.
- ربط كل نوع طباعة بعقد موحد يحدد القالب، دالة `PrintingService`، دالة الجسر، إعدادات الورق والطابعة، وسطح الطباعة.
- منع بناء HTML داخل واجهات المطعم.
- منع أي مسارات مباشرة مثل `QPrinter` أو `QPrintDialog` داخل ملفات المطعم.

## التغييرات

- إضافة `features.restaurant.restaurant_unified_printing_contract`.
- جعل `restaurant_printing_bridge` يرفق metadata صريحة: `print_surface=browser_html`، `print_document_type`، `print_route`، و `unified_printing=True`.
- توسيع alias routing: `kot` و `kitchen_ticket` و `customer_receipt` و `session_summary`.
- تسجيل Phase 305 داخل release gate.

## القاعدة

المطعم يملك قوالبه الخاصة، لكنه لا يملك محرك طباعة مستقل. كل الإخراج المرئي يمر عبر `printing.printing_service` و Browser HTML.
