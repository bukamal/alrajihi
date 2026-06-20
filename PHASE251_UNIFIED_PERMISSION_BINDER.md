# Phase 251 — Unified Permission Binder

## الهدف
ربط عقد Document Shell الذي أضيف في Phase 249 بصلاحيات التشغيل الفعلية في الواجهة، دون فرض إعادة تصميم كل الشاشات دفعة واحدة.

## ما تم
- إضافة `DocumentPermissionBinder` في `workspace/documents/document_permission_binder.py`.
- دعم أوامر موحدة: `view`, `create`, `update`, `save`, `delete`, `print`, `export`, `approve`, `cancel`.
- ربط صلاحيات `DocumentDescriptor` مع RBAC أولًا، ثم خريطة توافق مع `PermissionService` القديم، ثم سماح متوافق للثغرات المستقبلية حتى لا تنكسر الشاشات قبل نقلها.
- ربط `BaseDocumentTab` بطبقة الصلاحيات عبر:
  - `can_document_action(action)`
  - `document_permission_matrix()`
  - `apply_document_permissions()`
  - `permission_denied_message(action)`
- ربط `MainWindow` بحيث لا تستدعي أوامر `save/print/export` من شريط العمل العام إذا لم تسمح صلاحيات الوثيقة.
- ربط `UnifiedActionBar` ديناميكيًا عند تغيير التبويب.
- إضافة ربط best-effort لأزرار الوثائق الحالية مثل `save_btn`, `bottom_print_btn`, `bottom_export_btn`.
- تحديث `TransactionBottomActions` ليقبل تعطيل الأزرار بحسب action موحد.

## ملاحظات معمارية
هذه المرحلة لا تعني أن كل شاشة أصبحت بصريًا موحدة. معناها أن صلاحيات الأوامر الأساسية أصبحت تمر عبر عقد واحد قابل للفحص والاختبار، مع إبقاء الواجهات القديمة تعمل أثناء النقل التدريجي.

## التالي
Phase 252 يجب أن يركز على `MoneyDisplayPolicy` موحدة للأرقام والعملات في الجداول، المجاميع، الطباعة، التقارير، POS، المطعم، والسندات.
