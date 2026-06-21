# Phase 297 — Restaurant QSS Runtime Hotfix

## الهدف
إصلاح انهيار بدء التشغيل الناتج عن QSS داخل `alrajhi_client/theme/qss.py` بعد إضافة قواعد responsive الخاصة بالمطعم في Phase 296.

## المشكلة
كانت بعض قواعد QSS الجديدة داخل `build_global_qss()` مكتوبة بأقواس CSS مفردة داخل f-string، مثل:

```python
QToolButton#restaurantTableOperationsMenuButton {
```

وهذا يجعل Python يفسر `{ ... }` كجزء من f-string، فينتج خطأ وقت التشغيل مثل:

```text
NameError: name 'background' is not defined
```

## الإصلاح
تم تحويل أقواس CSS الجديدة إلى أقواس f-string صحيحة `{{` و `}}` لكل قواعد المطعم المضافة حديثًا، خصوصًا:

- `restaurantTableOperationsMenuButton`
- `restaurantOperationSplitter[restaurant_layout_mode="compact"]`
- `restaurantDashboard[restaurant_layout_mode="compact"]`
- `restaurantPOSWidget[restaurant_compact_mode="true"]`
- `restaurantOrderSummaryCard[restaurant_compact_mode="true"]`

## الحماية المضافة
أضيف اختبار مباشر يبني QSS للثيم الفاتح والداكن باستخدام `build_global_qss(get_tokens(...))` لضمان أن التطبيق لا ينهار أثناء `ThemeManager.apply_theme()`.

## النطاق
هذا Hotfix لا يضيف وظائف مطعم جديدة. يثبت تشغيل التطبيق ويحمي مسار الثيم من أخطاء f-string داخل QSS.

## تحسين إضافي في الاختبارات المعزولة
أضيف fallback للاستيراد داخل `alrajhi_client/gateways/local/restaurant_gateway.py` حتى يعمل عند تحميل الملف مباشرة في اختبارات `importlib.util.spec_from_file_location` حتى لو كان `features` موجودًا كـ module مؤقت غير package داخل `sys.modules`.
