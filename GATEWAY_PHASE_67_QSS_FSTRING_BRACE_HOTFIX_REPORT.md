# GATEWAY PHASE 67 - QSS F-String Brace Hotfix

## الهدف
إصلاح تعطل التطبيق عند بدء التشغيل بسبب تفسير أقواس QSS داخل f-string كتعابير Python.

## الخطأ المعالج
`NameError: name 'padding' is not defined` داخل:

- `alrajhi_client/theme/qss.py`
- `build_global_qss(colors)`

## سبب الخطأ
بعض محددات QSS كانت مكتوبة داخل f-string بأقواس مفردة مثل:

```css
QTableView::item, QTableWidget::item {
    padding: 6px;
}
```

في f-string يجب تهريب أقواس CSS إلى `{{` و `}}`، وإلا يحاول Python تفسير المحتوى ككود.

## الملفات المعدلة
- `alrajhi_client/theme/qss.py`

## الاختبارات المنفذة
- `python3 -m compileall -q alrajhi_client` ✅
- استدعاء `build_global_qss(get_tokens('light'))` ✅
- استدعاء `build_global_qss(get_tokens('dark'))` ✅
- `tools/verify_design_system.py` ✅
- `tools/verify_table_tab_design_system.py` ✅

## النتيجة
تم إصلاح تعطل بدء التشغيل الناتج عن QSS f-string، وتوليد الثيم يعمل للثيم الفاتح والداكن.
