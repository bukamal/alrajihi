# Phase 353 — Branded Login, Splash & Activation Runtime Polish

## الهدف
تطبيق الهوية البصرية عمليًا على شاشات بدء التشغيل، تسجيل الدخول، والتفعيل بدل الاكتفاء بطبقة الألوان العامة.

## ما تم

- إضافة عقد أولي PyQt-free لشاشات التشغيل الأولى:
  - `alrajhi_client/theme/first_run_identity.py`
- إضافة أدوات Runtime موحدة لبناء الأسطح ذات الهوية:
  - `alrajhi_client/ui/first_run_branding.py`
- تحويل تسجيل الدخول إلى واجهة مقسومة:
  - لوحة هوية يسار/يمين حسب اتجاه الواجهة.
  - لوحة نموذج مستقلة للحقول والأزرار.
  - زر دخول رئيسي موحد.
- تحويل التفعيل إلى واجهة مقسومة مشابهة:
  - لوحة هوية.
  - لوحة تفعيل.
  - بطاقة معلومات جهاز/ترخيص.
  - أزرار تفعيل/إعادة محاولة/إلغاء موحدة.
- تحسين شاشة التحميل:
  - أسماء ObjectName موحدة للـ progress والـ stage chips.
  - ربط السطح بسمة `firstRunSurface='splash'`.
- إضافة QSS خاص بالمرحلة:
  - `QFrame#firstRunBrandPanel`
  - `QFrame#firstRunFormPanel`
  - `QPushButton#firstRunPrimary`
  - `QFrame#activationDevicePanel`
  - `QProgressBar#firstRunProgressTrack`

## ملفات الحراسة

- `tools/phase353_branded_first_run_runtime_guard.py`
- `tests/test_phase353_branded_login_splash_activation_runtime.py`
- مخرجات التدقيق:
  - `tools/audit_outputs/branded_first_run_runtime_matrix.csv`
  - `tools/audit_outputs/branded_first_run_runtime_summary.json`

## سياسة التوحيد

أي تعديل لاحق على شاشات التحميل أو تسجيل الدخول أو التفعيل يجب أن يستخدم `first_run_branding.py` و tokens المركزية، وليس ألوانًا أو قياسات محلية متفرقة.
