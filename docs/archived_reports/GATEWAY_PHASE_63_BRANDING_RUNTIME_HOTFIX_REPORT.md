# GATEWAY PHASE 63 - Branding Runtime Hotfix

## الهدف
معالجة عدم ظهور شعارات المشروع داخل النسخة المبنية على Windows، ومعالجة فشل GitHub Actions بسبب UnicodeEncodeError في سكربت التحقق.

## السبب الفني
1. سكربت `tools/verify_branding_assets.py` كان يطبع رموز Unicode مثل ✅ و ❌، وبيئة Windows في GitHub Actions استخدمت ترميز CP1252، مما سبب فشل الطباعة.
2. مسار أصول العلامة التجارية داخل PyInstaller قد يختلف بين بيئة المصدر وبيئة التشغيل المجمّدة، لذلك تم جعل `brand_assets.py` يبحث في عدة مواقع محتملة داخل `_MEIPASS` و`_internal` ومجلد التنفيذ.
3. إعداد `company/logo_path` قد يحتوي مسارًا قديمًا غير موجود بعد التثبيت؛ أصبح `config.get_company_info()` يتحقق من وجود المسار ويعود تلقائيًا إلى شعار المشروع الافتراضي.
4. قوالب الطباعة أصبحت تتحقق من وجود الشعار قبل إدراجه، وتعود إلى شعار المشروع الافتراضي عند فقدان المسار المحفوظ.

## الملفات المعدلة
- `.github/workflows/build-windows-installer.yml`
- `tools/verify_branding_assets.py`
- `alrajhi_client/brand_assets.py`
- `alrajhi_client/config.py`
- `alrajhi_client/printing/print_templates.py`

## النتيجة
- الشعار يظهر من أصول المشروع في لوحة التحكم.
- الشعار يظهر افتراضيًا في الطباعة عند تفعيل `show_logo`.
- الإعدادات تعود إلى شعار المشروع إذا كان مسار الشعار المخزن غير صالح.
- GitHub Actions لا يفشل بسبب UnicodeEncodeError.
