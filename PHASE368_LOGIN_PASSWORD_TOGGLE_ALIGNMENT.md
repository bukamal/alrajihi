# PHASE368_LOGIN_PASSWORD_TOGGLE_ALIGNMENT

## الهدف
إصلاح تداخل زر إظهار/إخفاء كلمة المرور مع حقل كلمة المرور في شاشة تسجيل الدخول، مع الحفاظ على تصميم تسجيل الدخول المسترجع في Phase367 قبل Phase350.

## السبب الفني
في البنية المسترجعة كان حقل كلمة المرور وزر الإظهار داخل `QHBoxLayout` مباشر، لكن بدون سياسة حجم صريحة أو مسافة هندسية بينهما. مع اختلاف الخط أو DPI أو اتجاه RTL يمكن أن يبدو الزر كأنه يلامس الحقل أو يغطي حدّه/مساحة الرسم.

## الحل
- إبقاء `LoginDialog` على بطاقة واحدة بتخطيط `QVBoxLayout` مباشر.
- جعل حقل كلمة المرور عنصرًا متمدداً فقط: `QSizePolicy.Expanding, QSizePolicy.Fixed`.
- جعل زر إظهار/إخفاء كلمة المرور عنصرًا ثابتًا فقط: `QSizePolicy.Fixed, QSizePolicy.Fixed`.
- إضافة مسافة فعلية داخل `pwd_layout.setSpacing(10)`.
- إدخال الزر بمحاذاة عمودية `Qt.AlignVCenter`.
- ضبط QSS للزر بأبعاد ثابتة وصفر padding/margin حتى لا يتأثر بالأنماط العامة للأزرار.

## الملفات
- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/login_password_toggle_alignment_contract.py`
- `tools/phase368_login_password_toggle_alignment_guard.py`
- `tests/test_phase368_login_password_toggle_alignment.py`

## التحقق
- `python -m compileall`
- `tools/phase368_login_password_toggle_alignment_guard.py`
- اختبارات Phase 368
