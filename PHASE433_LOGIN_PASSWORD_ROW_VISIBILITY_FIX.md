# Phase 433 — Login Password Row Visibility Fix

## الهدف

إصلاح خلل Runtime في شاشة تسجيل الدخول الأفقية حيث يظهر عنوان `كلمة المرور` بينما يختفي حقل الإدخال نفسه أو ينضغط خلف صف اللغة/تذكر المستخدم.

## التغيير

- جعل صف كلمة المرور `loginPasswordRow` صفًا ثابتًا مرئيًا داخل `loginCredentialsPanel`.
- تحويل `pwd_row` المحلي إلى `self.password_row` حتى يمكن فرض مقاساته Runtime.
- إضافة سياسة صريحة: `loginPasswordPolicy="password_row_visible_fixed"`.
- إضافة مقاسات Runtime واضحة لحاوية بيانات الدخول وصف كلمة المرور وحقل كلمة المرور وزر العين.
- منع صف الخيارات من استهلاك مساحة صف كلمة المرور.
- عدم تغيير منطق تسجيل الدخول أو التفعيل أو تذكر المستخدم.

## الملفات المتأثرة

- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/login_password_row_visibility_fix_contract.py`
- `tools/phase433_login_password_row_visibility_guard.py`
- `tests/test_phase433_login_password_row_visibility_fix.py`

## قبول المرحلة

- يظهر حقل كلمة المرور فعليًا بين اسم المستخدم وصف اللغة.
- لا يغطي صف اللغة أو تذكر المستخدم حقل كلمة المرور.
- لا ينقص ارتفاع حاوية بيانات الدخول عن ارتفاع الصفوف المطلوبة.
- تبقى الواجهة أفقية وبهوية المشروع البصرية.
