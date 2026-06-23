# Phase 346 — Tab Lifecycle, Fixed Dashboard & Save-Without-Close Policy

## الهدف

توحيد معالجة ثلاث مشكلات تشغيلية في الـ shell:

1. لوحة التحكم لا تظهر كتبويب قابل للإغلاق.
2. عند إغلاق آخر تبويب لا تبقى مساحة بيضاء فارغة، بل يعود الـ shell إلى لوحة التحكم الثابتة.
3. أزرار الحفظ داخل التبويبات الرئيسية والفرعية تحفظ فقط، ولا تغلق التبويب.

## التغييرات

- تم تثبيت Dashboard داخل `QStackedWidget` كسطح ثابت `fixedDashboardSurface` بدلاً من إضافته إلى `TabbedWorkspace`.
- أصبح `switch_page('dashboard')` يعرض السطح الثابت مباشرة ولا يستدعي `open_singleton`.
- أصبح `TabbedWorkspace` يرفض فتح `dashboard` كتبويب عبر `FIXED_SURFACE_TAB_IDS`.
- عند إغلاق تبويب:
  - يتم اختيار التبويب السابق/التالي إن وجد.
  - إذا لم يبق أي تبويب، يتم إطلاق `emptyWorkspace` ليعيد `MainWindow` السطح الثابت للوحة التحكم.
- تم فصل مسار الحفظ عن مسار الإغلاق في التبويبات المضمنة، خصوصاً `DialogDocumentTab` ومرتجعات البيع/الشراء.
- تم تحويل أزرار الإغلاق القديمة التي كانت تستخدم `removeTab` مباشرة إلى `close_tab_at` عند توفره حتى يتم تنظيف metadata ومنع الواجهة البيضاء.

## الملفات الرئيسية

- `alrajhi_client/views/main_window.py`
- `alrajhi_client/shell/tab_workspace.py`
- `alrajhi_client/features/dialog_documents/dialog_document_tab.py`
- `alrajhi_client/features/returns/return_editor_tabs.py`
- `alrajhi_client/features/returns/components/return_actions.py`
- `alrajhi_client/workspace/shell/tab_lifecycle_contract.py`
- `tools/phase346_tab_lifecycle_dashboard_fallback_guard.py`
- `tests/test_phase346_tab_lifecycle_dashboard_fallback.py`

## الحارس

الحارس `phase346_tab_lifecycle_dashboard_fallback_guard.py` يتحقق من:

- أن Dashboard مثبت كسطح ثابت وليس تبويباً.
- أن Dashboard لا يحمل عنواناً بصرياً داخل شريط السياق.
- أن إغلاق آخر تبويب يعيد السطح الثابت.
- أن حفظ التبويب لا يستدعي `accept()` أو يغلق التبويب.
- أن المسارات القديمة التي تغلق التبويب تستخدم lifecycle موحداً.
