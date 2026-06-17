# SETTINGS PHASE 146 — Security, Audit & Governance Integration

## النطاق
استكمال وحدة الإعدادات بعد Phase 145 بإضافة طبقة حوكمة تشغيلية تربط الصلاحيات وسجل تغييرات الإعدادات بسلوك النظام الفعلي.

## الملفات المعدلة/المضافة

- `alrajhi_client/core/services/permission_service.py`
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/core/services/__init__.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/views/widgets/base_widget.py`
- `alrajhi_client/views/widgets/invoices_widget.py`

## المنفذ فعليًا

### 1. طبقة PermissionService
أضيفت خدمة مركزية جديدة:

- `permission_service.can(action)`
- `permission_service.should_hide_profit()`
- `permission_service.policy()`
- `permission_service.denied_message(action)`

الأفعال المدعومة حاليًا:

- `delete_records`
- `edit_invoices`
- `edit_returns`
- `view_reports`
- `export_reports`
- `hide_profit`

المدير `admin` مستثنى افتراضيًا من المنع التشغيلي.

### 2. إعدادات الصلاحيات داخل SettingsService
أضيفت:

- `get_security_settings()`
- `save_security_settings(...)`

المفاتيح الجديدة:

- `security/hide_profit_for_non_admin`
- `security/prevent_delete_for_non_admin`
- `security/prevent_invoice_edit_for_non_admin`
- `security/prevent_return_edit_for_non_admin`
- `security/restrict_reports_to_admin`
- `security/restrict_report_export_to_admin`
- `security/blocked_report_roles`

### 3. تبويب الصلاحيات في شاشة الإعدادات
أضيف تبويب جديد:

- `🔐 الصلاحيات`

ويحتوي على:

- إخفاء الربح عن غير المدير.
- منع الحذف عن غير المدير.
- منع تعديل الفواتير عن غير المدير.
- منع تعديل المرتجعات عن غير المدير.
- حصر التقارير بالمدير.
- حصر تصدير التقارير بالمدير.
- أدوار ممنوعة من التقارير بصيغة CSV.

### 4. تبويب سجل الإعدادات
أضيف تبويب جديد:

- `📜 سجل الإعدادات`

ويعرض آخر 200 تغيير من جدول:

- `settings_audit`

مع الأعمدة:

- الوقت.
- المفتاح.
- القيمة السابقة.
- القيمة الجديدة.
- المصدر.

### 5. تصدير/استيراد الإعدادات JSON
أضيفت إلى `SettingsService`:

- `export_settings_dict()`
- `import_settings_dict(payload)`

وأضيفت للواجهة أزرار:

- تصدير الإعدادات JSON.
- استيراد إعدادات JSON.

### 6. ربط الصلاحيات بسلوك فعلي
تم ربط الصلاحيات مباشرة في:

#### BaseWidget
- منع التصدير عند تعطيل تصدير التقارير.
- تعطيل أزرار التعديل/الحذف حسب السياسة.

#### InvoicesWidget
- منع تعديل الفواتير حسب السياسة.
- منع حذف الفواتير حسب السياسة.
- تعطيل أزرار التعديل/الحذف حسب السياسة.

## اختبار السلامة
تم تنفيذ compile على الملفات التالية بنجاح:

- `core/services/permission_service.py`
- `core/services/settings_service.py`
- `views/widgets/settings_widget.py`
- `views/widgets/base_widget.py`
- `views/widgets/invoices_widget.py`

الأمر المستخدم:

```bash
python -m compileall -q core/services/permission_service.py core/services/settings_service.py views/widgets/settings_widget.py views/widgets/base_widget.py views/widgets/invoices_widget.py
```

## النتيجة
أصبحت وحدة الإعدادات لا تحفظ بيانات فقط، بل تتحكم فعليًا في بعض سلوك النظام التشغيلي: الحذف، تعديل الفواتير، تصدير التقارير، وسجل تغييرات الإعدادات.

## توصية المرحلة التالية
Phase 147 يجب أن تركز على:

1. ربط `should_hide_profit()` بتقارير الربح والمبيعات.
2. ربط `ACTION_EDIT_RETURNS` بشاشات المرتجعات.
3. ربط `ACTION_VIEW_REPORTS` بدخول تبويب/وحدة التقارير.
4. إضافة شاشة إدارة مستخدمين وأدوار أكثر تفصيلاً لاحقًا بدل الاعتماد على role نصي فقط.
