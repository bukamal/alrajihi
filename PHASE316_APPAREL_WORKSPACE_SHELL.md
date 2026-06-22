# Phase 316 — Apparel Workspace Shell

## الهدف
إضافة واجهة ألبسة مستقلة ظاهريًا مبنية على أساس `item_variants` الذي أُضيف في Phase 315، بدون إنشاء محرك ألبسة مستقل أو خلط اللون/المقاس مع الوحدات الفرعية.

## النطاق
- إضافة صفحة تنقل رئيسية باسم `apparel` بعنوان الألبسة.
- ربط ظهورها بإعداد `apparel/enabled`.
- إضافة `ApparelWorkspaceWidget` لعرض مصفوفة اللون/المقاس/الباركود/SKU/الكمية.
- دعم بحث باركود Variant عبر `ProductService.item_by_barcode()` فقط.
- إضافة قسم إعدادات ألبسة مستقل.
- إضافة عقد UI يوضح أن الألبسة تستخدم Product Variants وليس محركًا مستقلًا.

## خارج النطاق
- لا يوجد `apparel_gateway.py` أو `apparel_repository.py` أو DAO خاص بالألبسة.
- لا يوجد بيع ألبسة خاص في هذه المرحلة.
- لا يتم تغيير منطق الوحدات الفرعية.

## الحوكمة
كل الوصول للبيانات يمر عبر `ProductService` ثم gateway/repository الحالي، والواجهة لا تحتوي SQL ولا تستورد DAO/Repository مباشرة.
