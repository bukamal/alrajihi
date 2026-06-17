# SETTINGS PHASE 148 — Configuration Profiles

## الهدف
تحويل الإعدادات من مجموعة واحدة ثابتة إلى ملفات إعدادات قابلة للتبديل حسب نمط التشغيل: Default، Retail، Wholesale، Manufacturing، Testing.

## المنفذ فعليًا

### 1. جداول Profiles
أضيفت الجداول التالية إلى المايغريشن:

- `settings_profiles`
- `settings_profile_values`

مع إنشاء ملف افتراضي `Default` تلقائيًا.

### 2. SettingsService Profile Awareness
تم تعديل `SettingsService.get()` ليقرأ قيمة الملف النشط أولًا، ثم يعود إلى جدول `settings` عند عدم وجود Override.

تم تعديل `SettingsService.set()` بحيث:

- إذا كان الملف النشط هو `Default`: يكتب في جدول `settings` كالسابق.
- إذا كان الملف النشط غير Default: يكتب في `settings_profile_values` كقيمة خاصة بالملف النشط.

### 3. عمليات Profiles
أضيفت دوال:

- `list_profiles()`
- `get_active_profile()`
- `create_profile()`
- `set_active_profile()`
- `clone_profile()`
- `export_profile_dict()`
- `import_profile_dict()`
- `profile_health()`

### 4. واجهة الإعدادات
أضيف تبويب جديد:

`🧩 ملفات الإعدادات`

ويحتوي على:

- عرض الملفات.
- إنشاء Profile.
- تفعيل Profile.
- نسخ Profile.
- تصدير Profile JSON.
- استيراد Profile JSON.
- عرض حالة الملف النشط وعدد الإعدادات الناقصة.

### 5. التشخيص
تم ربط صفحة التشخيص بعرض:

- اسم ملف الإعدادات النشط.
- عدد إعدادات الملف.
- الإعدادات الناقصة.

### 6. Audit
تغييرات الإعدادات داخل Profile غير Default تسجل في `settings_audit` بصيغة مفتاح:

`profile:<profile_name>:<setting_key>`

## ملاحظات تشغيلية
هذه المرحلة لا تضيف فروعًا ولا محاسبة ولا Workflow. هي فقط طبقة Profiles للإعدادات، لتجهيز المشروع للمرحلة التالية Multi-Branch Foundation.

## اختبار تقني
تم فحص Syntax للملفات المعدلة باستخدام `py_compile` بنجاح. لم يتم تشغيل الواجهة فعليًا داخل البيئة الحالية لأن PyQt5 غير مثبت في بيئة التنفيذ.
