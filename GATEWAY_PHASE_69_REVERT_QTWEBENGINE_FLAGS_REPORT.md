# GATEWAY PHASE 69 - REVERT QTWEBENGINE FLAGS HOTFIX

## السبب
بعد مقارنة الحزمة العاملة `login_hotfix-1(1).zip` مع Phase 68 ظهر أن الخطأ كان في إضافة دالة `configure_linux_qt_runtime()` داخل `alrajhi_client/main.py`.

الدالة أضافت متغيرات بيئة خاصة بـ QtWebEngine/Chromium:
- `QTWEBENGINE_CHROMIUM_FLAGS=--no-sandbox --disable-dev-shm-usage --disable-gpu`
- `QTWEBENGINE_DISABLE_SANDBOX=1`
- `QTWEBENGINE_DISABLE_ROOT_SANDBOX=1`

في بيئتك أدت هذه المتغيرات إلى الخطأ:
`error: expected absolute path: "--shm-helper"`
ثم انهيار `Segmentation fault`.

## الإصلاح
تم حذف دالة تهيئة QtWebEngine بالكامل والعودة إلى سلوك `main.py` الموجود في الحزمة العاملة، مع الإبقاء على تعديلات Phase 65/66/67 الخاصة بالثيم والجداول وإصلاح QSS.

## الملفات المعدلة
- `alrajhi_client/main.py`

## الاختبارات
- Python compileall: PASS
- build_global_qss light/dark: PASS
- verify_design_system: PASS
- verify_table_tab_design_system: PASS

## ملاحظة تشغيل
إذا ظهرت رسالة `XDG_RUNTIME_DIR not set` فقط فهي تحذير Linux شائع وليست سبب الانهيار. لا نضيف متغيرات WebEngine ما دام التطبيق يعمل بدونها.
