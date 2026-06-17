# SETTINGS PHASE 144 — Runtime Settings Integration

## الهدف
تحويل الإعدادات من شاشة تخزين قيم إلى طبقة تحكم فعلية تؤثر على سلوك الفواتير والمخزون والتشخيص.

## ما تم تطبيقه

### 1. Settings Runtime Helpers
تم توسيع `core/services/settings_service.py` بإضافات تشغيلية:

- `get_bool()`
- `get_int()`
- `get_decimal_places()`
- `get_invoice_settings()`
- `invoice_prefix(inv_type)`
- `get_inventory_settings()`
- `get_units_settings()`
- `get_language_settings()`
- `save_language_settings()`
- `company_info()`
- `audit_rows()`

النتيجة: الوحدات الأخرى تستطيع قراءة الإعدادات بصيغة typed بدل التعامل مع نصوص خام.

### 2. ربط بادئات أرقام الفواتير Runtime
تم تعديل `database/repositories/invoice_repo.py` بحيث يستخدم توليد أرقام الفواتير:

- `invoice/sales_prefix`
- `invoice/purchase_prefix`
- `invoice/number_width`

بدل الاعتماد على بادئة ثابتة داخل الكود.

### 3. منع المخزون السالب Runtime
تم تعديل `core/services/warehouse_service.py` بحيث يتحقق من إعداد:

- `inventory/allow_negative_stock`

عند تسجيل حركات فاتورة البيع. إذا كان الإعداد غير مفعل وكان الرصيد غير كافٍ، يتم منع العملية برسالة واضحة.

### 4. سجل تغييرات الإعدادات
تمت إضافة جدول جديد:

```sql
settings_audit
```

وتم تعديل `database/connection.py` بحيث يسجل تلقائيًا كل تغيير في الإعدادات مع:

- المفتاح
- القيمة السابقة
- القيمة الجديدة
- وقت التغيير
- المصدر

### 5. Migration آمن
تم تعديل `database/migrations.py` لإضافة:

- `settings_audit`
- `idx_settings_audit_key_time`

مع الحفاظ على توافق قواعد البيانات القديمة.

### 6. تشخيص متقدم
تمت إضافة `SystemService.integrity_checks()` لفحوصات read-only:

- مواد بمخزون سالب
- أرصدة مستودعات سالبة
- فواتير بلا أسطر
- أسطر فواتير يتيمة
- فواتير بيع بعميل مفقود
- فواتير شراء بمورد مفقود
- مكونات BOM مكسورة
- عدد سجلات settings_audit
- SQLite quick_check

### 7. صفحة التشخيص
تم توسيع صفحة التشخيص في `settings_widget.py` لعرض:

- نتائج فحص الاتساق المتقدم
- مجموع المخاطر
- آخر 10 تغييرات في الإعدادات

## الملفات المعدلة

- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/core/services/system_service.py`
- `alrajhi_client/core/services/warehouse_service.py`
- `alrajhi_client/database/connection.py`
- `alrajhi_client/database/migrations.py`
- `alrajhi_client/database/repositories/invoice_repo.py`
- `alrajhi_client/views/widgets/settings_widget.py`

## فحص السلامة
تم تنفيذ compile على الملفات المعدلة بنجاح.

## ملاحظات مهمة
هذه المرحلة لم تضف صلاحيات أو محاسبة؛ ركزت على الربط التشغيلي للإعدادات الحالية. المرحلة التالية المقترحة هي ربط إعدادات الطباعة والشركة داخل HTML/PDF templates بشكل كامل.
