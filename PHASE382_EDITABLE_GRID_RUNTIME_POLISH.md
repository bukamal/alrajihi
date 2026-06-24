# Phase 382 — Editable Grid Runtime Polish

## الهدف
تثبيت تجربة إدخال الجداول التحريرية بعد توحيد الـ inline ومحررات الوثائق.

## ما تغيّر
- عمود المادة/الصنف/المنتج يبقى نقطة البداية الرسمية للإدخال.
- عمود الباركود صار يستخدم نفس Delegate الخاص بالمادة، لذلك إدخال الباركود داخل الخلية يحاول حل المادة والوحدة والبيانات المرتبطة بدل حفظ نص خام فقط.
- عند إغلاق محرر المادة أو الباركود ينتقل المؤشر مباشرة إلى الكمية ويفتح تحريرها.
- زر إضافة سطر في الفواتير، التحويل المستودعي، وBOM يركز السطر الجديد، لا أول سطر في الجدول.
- جداول الفواتير تستخدم تحديد الخلية الحالية بدل تحديد الصف بالكامل، مع إبقاء شاشات اللمس مثل POS/المطعم قادرة على اختيار الصف.

## ملفات رئيسية
- `alrajhi_client/ui/table_keyboard_policy.py`
- `alrajhi_client/features/transactions/grids/transaction_line_grid.py`
- `alrajhi_client/features/transactions/transaction_document_tab.py`
- `alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py`
- `alrajhi_client/features/manufacturing/bom_document_tab.py`

## الحماية
- `tools/phase382_editable_grid_runtime_polish_guard.py`
- `tests/test_phase382_editable_grid_runtime_polish.py`
- `alrajhi_client/workspace/quality/editable_grid_runtime_polish_contract.py`
