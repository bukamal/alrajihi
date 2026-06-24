# Phase 379 — Inline Party Layout Unification

## الهدف
توحيد هيكلية محرر العميل والمورد داخل نفس التبويب، وإزالة البطاقة العلوية التي كانت تعرض عنوان المستند مثل "عميل" أو "مورد" داخل الـ inline، وتوسيع منطقة التحرير أفقياً.

## التغييرات
- إضافة `PartyInlineEditorHostMixin` كمضيف موحد لواجهتي العملاء والموردين.
- جعل العملاء والموردين يستخدمان نفس مسار `_install_party_inline_host` ونفس `_show_inline_party_editor`.
- إزالة `inline_title_label` و `InlineEditorTitle` من مضيف العميل/المورد.
- جعل `PartyEditorTab` يدعم `inline_mode=True`.
- عند `inline_mode=True` لا يتم عرض `DocumentHeaderCard` داخل المحرر.
- توسيع لوحة التفاصيل بإعداد `ResponsiveMasterDetail(..., master_weight=2, detail_weight=3)`.

## الحماية
- `tools/phase379_inline_party_layout_unification_guard.py`
- `tests/test_phase379_inline_party_layout_unification.py`
- `alrajhi_client/workspace/quality/inline_party_layout_unification_contract.py`
