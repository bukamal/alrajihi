# GATEWAY PHASE 68 - Linux Qt Runtime Hotfix

## الهدف
معالجة الانهيار عند تشغيل التطبيق على Linux/root بسبب رسائل Qt/Chromium:

- `error: expected absolute path: "--shm-helper"`
- `QStandardPaths: XDG_RUNTIME_DIR not set`
- `Segmentation fault`

## التشخيص
الانهيار ليس من QSS أو ThemeManager مباشرة. يحدث قبل اكتمال تشغيل الواجهة في بيئات Linux محدودة/Root بسبب إعدادات Qt runtime و/أو QtWebEngine/Chromium sandbox وغياب XDG runtime directory.

## التعديل
تم تعديل:

- `alrajhi_client/main.py`

وإضافة دالة:

- `configure_linux_qt_runtime()`

وتُستدعى قبل أي import من PyQt5.

## ما تضبطه الدالة

- إنشاء `XDG_RUNTIME_DIR` عند غيابه مع صلاحيات `0700`.
- إضافة Chromium flags:
  - `--no-sandbox`
  - `--disable-dev-shm-usage`
  - `--disable-gpu`
- تعطيل WebEngine sandbox عند التشغيل كـ root:
  - `QTWEBENGINE_DISABLE_SANDBOX=1`
  - `QTWEBENGINE_DISABLE_ROOT_SANDBOX=1`
- فرض rendering آمن:
  - `QT_OPENGL=software`

## الاختبار

- `python3 -m py_compile alrajhi_client/main.py` ✅
- `python3 -m compileall -q alrajhi_client tools` ✅

## ملاحظة تشغيل
إذا بقيت المشكلة على سيرفر بلا واجهة رسومية، شغّل التطبيق عبر X server/VNC أو:

```bash
export QT_QPA_PLATFORM=xcb
python3 alrajhi_client/main.py
```

للاختبار دون واجهة يمكن استخدام:

```bash
export QT_QPA_PLATFORM=offscreen
python3 alrajhi_client/main.py
```

لكن التشغيل الحقيقي للبرنامج المكتبي يحتاج بيئة عرض رسومية.
