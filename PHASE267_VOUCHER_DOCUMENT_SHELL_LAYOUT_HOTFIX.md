# Phase 267 — Voucher Document Shell Layout Hotfix

## الهدف
إصلاح واجهة إضافة/تعديل السندات التي ظهرت فيها الحقول مكدسة تحت بعضها داخل الشاشة، خصوصًا عند إنشاء سند قبض/دفع جديد.

## السبب الفني
مكونات السند كانت تستخدم `QFormLayout` تقليديًا داخل ثلاث بطاقات متتالية. إضافة إلى ذلك، عند تغيير نوع السند كان الكود يخفي الحقول فقط مثل العميل/المورد أو الصندوق/الحساب البنكي، لكنه لا يخفي labels المرتبطة بها. النتيجة كانت صفوفًا فارغة أو labels ظاهرة بلا حقول، وشكلًا غير موحد مع Document Shell.

## الإصلاح
- تحويل `VoucherHeaderPanel` إلى `QGridLayout` مضغوط بعمودين.
- تحويل `VoucherLinkPanel` إلى `QGridLayout` مضغوط.
- تحويل `VoucherPaymentPanel` إلى `QGridLayout` مضغوط.
- إضافة آلية `_set_field_visible()` لإخفاء label والحقل معًا.
- الحفاظ على API القديم: `payload()`, `load()`, `voucher_type()`, `amount_usd()`.
- الإبقاء على `VoucherEditorTab` كـ Document Shell رسمي مع `VoucherActionsPanel` داخل `BottomActionBar`.

## النتيجة
واجهة السند أصبحت أقرب إلى باقي Document Shells، والحقول لم تعد تتكدس أو تترك labels فارغة عند تغيير نوع السند أو طريقة الدفع.
