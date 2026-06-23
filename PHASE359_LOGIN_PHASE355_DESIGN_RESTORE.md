# Phase 359 — Login Phase355 Design Restore

## الهدف
إرجاع تصميم واجهة تسجيل الدخول فقط إلى تصميم Phase 355 بعد أن ظهر تخطيط Phase 358 مشوّهًا ومتداخلًا في بيئة التشغيل.

## النطاق
- تم إرجاع `LoginDialog` إلى تخطيط Phase 355 ذي اللوحة الجانبية للهوية + بطاقة نموذج تسجيل الدخول.
- لم يتم التراجع عن تحسينات المراحل اللاحقة الخاصة بالتبويبات، الجداول، النوافذ، QSS runtime safety، أو دورة حياة الإغلاق.
- بقيت شاشة التحميل والتفعيل وشاشات النظام الأخرى كما هي بعد المراحل اللاحقة.

## الملفات
- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/workspace/quality/login_phase355_restore_contract.py`
- `tools/phase359_login_phase355_restore_guard.py`
- `tests/test_phase359_login_phase355_restore.py`

## القاعدة
أي تعديل لاحق على تسجيل الدخول يجب ألا يعيد التخطيط المتداخل أو يخلط بين تصميم تسجيل الدخول وبقية شاشات first-run.
