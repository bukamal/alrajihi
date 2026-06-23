# Phase 357 — QSS Runtime Safety Hotfix

## الهدف

إصلاح خطأ تشغيل مباشر ظهر أثناء `ThemeManager.init_app()` بسبب أقواس CSS غير مهربة داخل f-string في `theme/qss.py`.

## المشكلة

كتل Phase 354 داخل `build_global_qss()` احتوت على أقواس CSS مفردة مثل:

```css
QTabWidget#TabbedWorkspace::pane {
```

وبما أن النص داخل Python f-string، حاول Python تفسير محتوى CSS كتعبير، فظهر الخطأ:

```text
NameError: name 'border' is not defined
```

## الإصلاح

- تهريب أقواس CSS الحرفية في كتلة التبويبات والقوائم وشريط الإجراءات.
- إضافة عقد تدقيق PyQt-free يولد QSS فعليًا للثيمين light/dark.
- إضافة guard يمنع تكرار أي خطأ runtime مشابه لا يظهر في compileall.

## الملفات

- `alrajhi_client/theme/qss.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/workspace/quality/qss_runtime_safety_contract.py`
- `tools/phase357_qss_runtime_safety_hotfix_guard.py`
- `tests/test_phase357_qss_runtime_safety_hotfix.py`

## النتيجة

أصبح `build_global_qss(get_tokens("light"))` و `build_global_qss(get_tokens("dark"))` يعملان بدون NameError، وبالتالي يمكن بدء التطبيق وتطبيق ThemeManager بأمان.
