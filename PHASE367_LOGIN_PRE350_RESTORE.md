# PHASE367_LOGIN_PRE350_RESTORE

## الهدف
إرجاع تصميم شاشة تسجيل الدخول فقط إلى البنية الأصلية قبل Phase 350، بعد أن تسببت تجارب Phase 352 وما بعدها في تداخل حقل كلمة المرور مع لوحة تذكر المستخدم/اللغة على بعض إعدادات الخط/الدقة.

## التحليل
سبب التداخل لم يكن كلمة المرور نفسها، بل إدخال لوحات داخلية ذات ارتفاعات ثابتة وخصائص QSS لاحقة مثل `loginCredentialsPanel`, `loginOptionsPanel`, `loginPasswordRow`, و `loginPasswordSafeSpacer`. هذه العناصر جعلت الرسم واحتساب المساحة في Qt غير متطابقين في بعض الحالات.

## القرار
إرجاع `LoginDialog` إلى التصميم الأصلي قبل Phase 350:

- بطاقة واحدة `loginCard`.
- `QVBoxLayout` مباشر.
- حقل المستخدم مباشرة داخل البطاقة.
- صف كلمة المرور المباشر `QHBoxLayout`.
- صف تذكر المستخدم/اللغة المباشر `QHBoxLayout`.
- لا توجد لوحات split أو fixed-height login panels.

## الحدود
لم يتم التراجع عن بقية المشروع أو عن الهوية العامة، الجداول، النوافذ، التبويبات، أو إصلاحات QSS. التراجع محصور في `alrajhi_client/views/dialogs/login_dialog.py` مع عقد تدقيق Phase 367.

## ملفات المرحلة

- `alrajhi_client/workspace/quality/login_pre350_restore_contract.py`
- `tools/phase367_login_pre350_restore_guard.py`
- `tests/test_phase367_login_pre350_restore.py`
