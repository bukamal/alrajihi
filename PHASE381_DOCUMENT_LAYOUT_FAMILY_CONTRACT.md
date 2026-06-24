# Phase 381 — Document Layout Family Contract

## الهدف

توحيد محررات المستندات حسب الوظيفة بدل ترك كل محرر يقرر شكله بشكل مستقل.

## العائلات المعتمدة

1. `card_form`
   - عميل، مورد، مستخدم، تصنيف، مستودع، فرع، صندوق، حساب بنك، مادة.
   - نموذج بيانات بسيط، واسع داخل الـ inline، بلا بطاقة عنوان مكررة.

2. `financial_document`
   - سند قبض، سند دفع، سند مصروف/مصروف.
   - بيانات مالية + ملخص مالي جانبي.

3. `tabular_document`
   - مبيعات، مشتريات، مرتجعات، تحويل مستودعي، BOM، أمر إنتاج.
   - جدول تحرير هو المساحة الأساسية، مع ملخص/أدوات جانبية.

## التغييرات

- إضافة `workspace/documents/document_layout_policy.py`.
- إضافة `BaseDocumentTab.apply_document_layout_profile()`.
- تطبيق السياسة تلقائيًا عند عرض أي مستند.
- ربط `UnifiedInlineWorkspaceMixin` بالسياسة الجديدة عند فتح أي محرر inline.
- إخفاء بطاقات العنوان المكررة داخل inline عبر سياسة واحدة.
- توحيد خصائص Runtime inspectable:
  - `documentLayoutKind`
  - `documentInlineMode`
  - `documentLayoutManaged`

## الأثر

كل inline أو مستند جديد يجب أن يقع ضمن عائلة وظيفية واضحة. هذا يمنع عودة مشكلة: محرر يفتح كتويب، محرر آخر كنافذة، محرر ثالث inline بحجم وشكل مختلف.
