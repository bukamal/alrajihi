# GATEWAY PHASE 76 — LANGUAGE SYSTEM FOUNDATION

## الهدف
تأسيس نظام لغات مركزي للمشروع وفق الترتيب المطلوب:

1. العربية — اللغة الأساسية والافتراضية، RTL.
2. الألمانية — اللغة الثانية، LTR.
3. الإنجليزية — اللغة الثالثة، LTR.

## ما تم تنفيذه

- تحديث `alrajhi_client/i18n/translator.py` ليصبح سجل اللغات المركزي.
- إضافة دعم ألماني أولي للمفاتيح الأساسية.
- إبقاء العربية كمصدر افتراضي لأي مفتاح ناقص.
- إزالة الفرنسية من واجهة اختيار اللغة في شاشة الدخول.
- أي قيمة قديمة `fr` أو `Français` يتم تحويلها تلقائيًا إلى العربية عبر `normalize_language()`.
- ربط شاشة الدخول بسجل اللغات المركزي بدل قائمة ثابتة.
- ربط تبويب المظهر في الإعدادات باختيار اللغة وحفظها في `settings.language`.
- إضافة `SettingsService.set_language()` لتخزين اللغة مع Audit Log.
- ضبط اتجاه الواجهة حسب اللغة:
  - العربية: `Qt.RightToLeft`
  - الألمانية/الإنجليزية: `Qt.LeftToRight`
- إصلاح قالب الطباعة الأساسي ليستخدم اتجاه اللغة بدل `ltr` الثابت مع `lang='ar'`.
- إضافة أداة تحقق: `tools/verify_language_foundation.py`.

## الملفات المعدلة

- `alrajhi_client/i18n/translator.py`
- `alrajhi_client/i18n/__init__.py`
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/views/main_window.py`
- `alrajhi_client/printing/print_templates.py`
- `tools/verify_language_foundation.py`

## الاختبارات

- `python3 tools/verify_language_foundation.py` ✅
- `python3 -m compileall -q alrajhi_client` ✅

## حدود هذه المرحلة

هذه مرحلة تأسيسية. لم يتم تحويل كل النصوص المباشرة في جميع الشاشات إلى مفاتيح ترجمة بعد. المرحلة التالية يجب أن تكون تحويلًا تدريجيًا للشاشات الأكثر استخدامًا إلى `translate(...)`، بدءًا من:

1. لوحة التحكم.
2. شريط التنقل والقوائم.
3. الفواتير والمبيعات والمشتريات.
4. المستودعات والمواد.
5. المرتجعات.
6. التقارير والطباعة التفصيلية.

## ملاحظة عملية

بعد تغيير اللغة من الإعدادات قد تحتاج بعض الشاشات لإعادة فتح أو إعادة تشغيل البرنامج حتى تتبدل كل النصوص، لأن المشروع لا يزال يحتوي نصوصًا مباشرة داخل Widgets كثيرة.
