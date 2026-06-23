# PHASE350 — Internal Close Button Tab Lifecycle

## الهدف

توحيد أزرار الإغلاق الداخلية داخل واجهات إنشاء الفواتير والمرتجعات مع زر X الموجود على التبويب نفسه.

## المشكلة

بعض أزرار الإغلاق داخل شاشة المستند كانت تستدعي `QWidget.close()` أو `QDialog.accept()` على الواجهة المضمنة. هذا قد يخفي محتوى التبويب فقط ولا يغلق التبويب كاملاً، فتظهر مساحة بيضاء أو لا تظهر رسالة تأكيد الإغلاق التي تظهر عند الضغط على X الخاص بالتبويب.

## السياسة الموحدة

- زر الإغلاق داخل المستند لا يغلق الودجت مباشرة.
- كل إغلاق داخلي يمر عبر `close_owning_workspace_tab()`.
- الإغلاق النهائي يمر عبر `TabbedWorkspace.close_tab_at()`.
- رسالة تأكيد التغييرات غير المحفوظة تبقى مملوكة لمسار التبويب نفسه.
- عند إغلاق آخر تبويب يتم الرجوع إلى Dashboard الثابتة بدون مساحة بيضاء.

## الملفات الرئيسية

- `alrajhi_client/workspace/shell/workspace_tab_close.py`
- `alrajhi_client/workspace/documents/base_document_tab.py`
- `alrajhi_client/features/transactions/transaction_document_tab.py`
- `alrajhi_client/features/returns/return_editor_tabs.py`
- `tools/phase350_internal_close_button_tab_lifecycle_guard.py`
- `tests/test_phase350_internal_close_button_tab_lifecycle.py`
