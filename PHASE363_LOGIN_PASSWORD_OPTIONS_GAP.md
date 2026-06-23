# Phase 363 — Login Password / Options Gap

## الهدف

إضافة مباعدة رأسية فعلية بين صف كلمة المرور ولوحة **تذكر المستخدم / اللغة** في شاشة تسجيل الدخول RTL، بعد ملاحظة أن اللوحة السفلية ما زالت تقترب بصريًا من حقل كلمة المرور أو تغطيه على بعض المقاسات/الثيمات.

## التغييرات

- رفع مقاييس شاشة تسجيل الدخول الرأسية في `theme/brand.py`.
- إضافة `login_password_bottom_gap` كمقياس رسمي.
- إضافة سياسة `loginSpacingPolicy="password_options_gap"` على بطاقة تسجيل الدخول.
- جعل قسم بيانات الدخول وقسم الخيارات بارتفاع ثابت صريح.
- إضافة `credentials_layout.addSpacing(...)` بعد صف كلمة المرور مباشرة.
- زيادة `login_section_gap` بين بطاقة بيانات الدخول وبطاقة الخيارات.
- تحديث QSS ليدعم سياسة المباعدة الجديدة عند توليد الثيمين light/dark.

## الملفات الرئيسية

- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/login_password_gap_contract.py`
- `tools/phase363_login_password_gap_guard.py`
- `tests/test_phase363_login_password_gap.py`

## ملاحظة تشغيلية

هذا الإصلاح لا يغير منطق تسجيل الدخول، ولا يعيد تصميم الشاشة بالكامل. التغيير مخصص للمباعدة الرأسية ومنع تغطية حقل كلمة المرور من المكون الذي تحته.
