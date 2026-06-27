# Phase 393 — Language Runtime Switch Hotfix

## الهدف
منع انهيار الواجهة أثناء تبديل اللغة بسبب تداخل تحديث الواجهة مع إشارات Qt، ومنع تكرار `sys.excepthook` عند وقوع `RecursionError`.

## الإصلاحات
- جعل تغيير اللغة في إعدادات الواجهة محميًا من إعادة الدخول `_language_change_in_progress`.
- تأجيل إعادة بناء القوائم والشريط العلوي عبر `QTimer.singleShot(0, ...)` حتى لا يحدث التحديث داخل call stack الخاص بالـ ComboBox.
- تحديث حالة اللغة في `MainWindow` قبل إعادة بناء القوائم.
- إضافة نفس مبدأ الحماية في شاشة تسجيل الدخول.
- جعل `install_offline_exception_hook()` idempotent حتى لا يلف `sys.excepthook` نفسه مرات متعددة.
- عند حدوث `RecursionError` يتم تمريره مباشرة إلى `sys.__excepthook__` بدل سلسلة hooks قد تكرر الخطأ.
- إضافة re-entry guard لتحميل ترجمات الفرنسية، مع مفاتيح حفظ إعدادات اللغة في ar/de/en/fr.

## التحقق
- `tools/phase393_language_runtime_switch_guard.py`
- `tests/test_phase393_language_runtime_switch.py`
