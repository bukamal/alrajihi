# PHASE377_INLINE_MANAGEMENT_EDITOR

## الهدف
توحيد واجهات إدارة المستخدمين، التصنيفات، المستودعات، والفروع مع هيكلية العملاء والموردين والسندات: زر الإضافة والتعديل لا يفتح تبويبًا فرعيًا جديدًا، بل يفتح محررًا مدمجًا داخل نفس التبويب بنمط Master-Detail.

## النطاق
- `UsersWidget`
- `CategoriesWidget`
- `WarehousesWidget` لإضافة/تعديل المستودع، مع منع تحويل المخزون من فتح تبويب فرعي.
- `BranchesWidget`

## التنفيذ
أضيفت طبقة مشتركة:

- `alrajhi_client/views/widgets/inline_document_host.py`

وتستخدم:

- `ResponsiveMasterDetail`
- `DetailPlaceholder`
- صفحة محرر داخلية `inline_editor_page`
- مضيف محرر داخلي `inline_editor_host`

## السياسة
- الإضافة والتعديل يتمان داخل نفس تبويب القائمة.
- الحفظ يحدث داخل المحرر ثم ينعش القائمة ويرجع للمعاينة.
- زر الإغلاق داخل المحرر يغلق لوحة التفاصيل فقط ولا يغلق تبويب القائمة.
- مسارات `open_*_document` تبقى كمسارات عالمية من القوائم/الاختصارات، لكنها لا تستعمل من أزرار الإضافة داخل القوائم المذكورة.

## التحقق
- `tools/phase377_inline_management_editor_guard.py`
- `tests/test_phase377_inline_management_editor.py`
