# PHASE362 — LOGIN PASSWORD OPTIONS NO OVERLAP

## الهدف
إصلاح تداخل لوحة "تذكر المستخدم / اللغة" مع حقل كلمة المرور في شاشة تسجيل الدخول العربية RTL.

## السبب
بعد توسيع شاشة الدخول عموديًا في Phase361 بقيت لوحة بيانات الدخول ولوحة الخيارات مرنتين داخل نفس التدفق الرأسي. في بعض أحجام النافذة أو مع النص العربي قد تضغط لوحة الخيارات على منطقة كلمة المرور بصريًا.

## التعديل
- جعل لوحة بيانات الدخول `loginCredentialsPanel` قسمًا ثابت الارتفاع داخل التخطيط.
- جعل لوحة الخيارات `loginOptionsPanel` قسمًا ثابت الارتفاع أسفل بيانات الدخول.
- إضافة مسافة إلزامية بين القسمين عبر `login_section_gap`.
- رفع ارتفاع شاشة الدخول وبطاقة النموذج حتى تستوعب الأقسام دون ضغط.
- إضافة الخاصية `loginOverlapPolicy="sectioned_no_overlap"` لتثبيت السياسة عبر QSS والاختبارات.

## الملفات الأساسية
- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/login_no_overlap_contract.py`
- `tools/phase362_login_no_overlap_guard.py`
- `tests/test_phase362_login_no_overlap.py`
