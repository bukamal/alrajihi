# PHASE366 — Login Pre-Phase352 RTL Safe Restore

## الهدف

إرجاع بنية شاشة تسجيل الدخول إلى التصميم الأصلي المستقر قبل Phase352، ثم تطبيق تحسينات RTL من Phase360 بطريقة آمنة لا تنتج تداخلًا بين حقل كلمة المرور ومكوّن **تذكر المستخدم / اللغة**.

## تحليل سبب التداخل

المحاولات بين Phase360 وPhase364 أدخلت تقسيمًا بصريًا يعتمد على Panels داخلية مثل `loginCredentialsPanel` و `loginOptionsPanel` مع ارتفاعات ثابتة وخصائص QSS مثل margins و density. في Qt، الـ layout يحجز المساحة حسب widgets/layouts، بينما بعض تأثيرات QSS تغيّر حدود الرسم فقط. عند اختلاف الخط أو DPI أو الترجمة العربية، بقيت مساحة الـ panel الفعلية أصغر من المحتوى، فظهر قسم الخيارات فوق صف كلمة المرور أو قريبًا منه بصريًا.

المشكلة لم تكن في المسافة نفسها فقط، بل في الاعتماد على **QSS margin/fixed panel geometry** بدل حجز مساحة فعلية داخل `QVBoxLayout`.

## الحل

- إعادة `LoginDialog` إلى بنية البطاقة الواحدة الأصلية قبل Phase352.
- إزالة الاعتماد على `firstRunBrandPanel`, `firstRunFormPanel`, `loginCredentialsPanel`, `loginOptionsPanel`, `loginPasswordRow`, و `loginPasswordSafeSpacer` داخل شاشة تسجيل الدخول.
- تطبيق تحسينات Phase360 بشكل آمن:
  - labels صريحة لاسم المستخدم وكلمة المرور.
  - RTL/LTR alignment حسب اللغة.
  - صف كلمة المرور يبقى `QHBoxLayout` مباشرًا داخل البطاقة.
  - صف التذكر/اللغة يبقى `QHBoxLayout` مباشرًا داخل البطاقة.
  - إضافة `layout.addSpacing(18)` كمسافة هندسية حقيقية بين كلمة المرور والخيارات.

## الملفات المتأثرة

- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/login_pre352_rtl_safe_contract.py`
- `tools/phase366_login_pre352_rtl_safe_guard.py`
- `tests/test_phase366_login_pre352_rtl_safe.py`
- `alrajhi_client/workspace/quality/release_gate_contract.py`

## التحقق

الحارس الخاص بالمرحلة يتحقق من أن شاشة الدخول تستخدم بنية Pre-Phase352، وأن تحسينات RTL موجودة، وأن علامات التداخل السابقة غير مستخدمة داخل `LoginDialog`.
