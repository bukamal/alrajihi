# PHASE364_LOGIN_PASSWORD_VISIBILITY_RESERVED_ROW

## الهدف

إصلاح بقاء حقل كلمة المرور مغطى جزئيًا بواسطة لوحة **تذكر المستخدم / اللغة** في شاشة تسجيل الدخول RTL.

## سبب الخلل

معالجة Phase363 اعتمدت على `margin-bottom` في QSS وعلى مسافات عامة داخل التخطيط. بعض أنماط Qt لا تجعل margin الخاص بـ `QLineEdit` مساحة حقيقية داخل `QVBoxLayout`، فيبقى الرسم البصري للوحة التالية قريبًا جدًا من حقل كلمة المرور أو فوقه عند اختلاف الخط/الثيم/الدقة.

## الحل

- وضع حقل كلمة المرور وزر إظهار/إخفاء داخل صف مستقل: `loginPasswordRow`.
- إضافة spacer widget فعلي داخل نفس layout: `loginPasswordSafeSpacer`.
- رفع ارتفاع لوحة بيانات الدخول إلى `356px`.
- رفع ارتفاع حقل الإدخال إلى `52px`.
- رفع المسافة بين بيانات الدخول وخيارات تذكر المستخدم/اللغة إلى `38px`.
- استخدام سياسة جديدة: `loginSpacingPolicy="password_row_reserved_gap"`.

## الملفات

- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/login_password_visibility_contract.py`
- `tools/phase364_login_password_visibility_guard.py`
- `tests/test_phase364_login_password_visibility.py`
