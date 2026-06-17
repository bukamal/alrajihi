# GATEWAY PHASE 73 — Safe Table/Tab Design System Coverage

## الهدف
تطبيق هوية الراجحي البصرية على الجداول، جداول النوافذ، والجداول داخل التبويبات، مع الالتزام بالأسلوب الآمن المستخدم في Phase 72.

## قاعدة السلامة
لم يتم استخدام أي من التالي:
- EventFilter عام.
- Runtime widget polish عام.
- أي QtWebEngine أو Chromium flags.
- أي تعديل على تهيئة Linux/root runtime.

## الملفات المعدلة
- `alrajhi_client/theme/qss.py`
  - إضافة تغطية مركزية أوسع لـ `QAbstractItemView`, `QTableView`, `QTableWidget`, `QTreeView`, `QTreeWidget`.
  - إضافة تغطية خاصة للجداول داخل `QTabWidget` وداخل `QDialog`.
  - توحيد `QHeaderView::section` وفق ألوان الهوية.
  - توحيد خلفيات محتوى التبويبات والبطاقات داخلها.

- `alrajhi_client/views/widgets/modern_ui.py`
  - استبدال QSS hard-coded بدالة `_modern_widget_style()` التي تقرأ من `ThemeManager.colors()`.
  - بقاء التطبيق محليًا للصفحات/الحوارات التي تستدعي `apply_modern_widget/apply_modern_dialog` فقط.

- `alrajhi_client/views/widgets/invoices_widget.py`
  - تحديث تنسيق فواتير البيع والشراء ليستخدم Design System.
  - توحيد الجداول والتبويبات داخل هذه الشاشة.

- `alrajhi_client/views/dialogs/invoice_dialog.py`
  - تحديث جدول بنود الفاتورة داخل النافذة إلى ألوان الهوية.

- `alrajhi_client/views/dialogs/item_dialog.py`
  - تحديث جدول وحدات المادة داخل النافذة إلى ألوان الهوية.

- `alrajhi_client/views/widgets/settings_widget.py`
  - تحديث تبويبات الإعدادات وجدول العملات وفق الهوية.

- `tools/verify_table_tab_design_system_safe.py`
  - Guard ساكن للتأكد من وجود تغطية Phase 73.

## نتيجة الاختبارات
- `python3 tools/verify_table_tab_design_system_safe.py`: OK
- `python3 -m compileall -q alrajhi_client tools`: OK

## ملاحظة تنفيذية
هذه المرحلة لا تدعي تعديل كل widget يدويًا، بل تطبق الهوية بأمان عبر QSS مركزي ومحلي في المواضع التي كانت تملك QSS متعارضًا. هذا يقلل خطر الانهيار الذي ظهر بعد Phase 66.
