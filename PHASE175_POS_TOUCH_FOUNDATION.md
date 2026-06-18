# Phase 175 — POS Touch Foundation

## الهدف

تحويل POS من شاشة بيع سريعة مستقلة نسبيًا إلى واجهة لمس مبنية على عقود المشروع الموحدة:

- الباركود الموحد عبر `barcode_input_service`
- باركود المادة وباركود الوحدة عبر نفس lookup
- الوحدات ومعاملات التحويل داخل سلة POS
- الإعدادات عبر `settings_service`
- تفضيلات الواجهة لكل مستخدم/فرع/profile
- الصلاحيات عبر `permission_service` و RBAC
- الترجمة العربية/الألمانية/الإنجليزية

## التغييرات الأساسية

### 1. POSService أصبح unit-barcode aware

تم تعديل:

```text
alrajhi_client/core/services/pos_service.py
```

الآن `POSService.add_scan()` يستخدم:

```python
barcode_input_service.lookup_entry(code, mode=mode)
```

بدل البحث المباشر أو fallback النصي الخطر.

إذا كان الباركود يخص وحدة فرعية، يتم حفظ:

```text
unit_id
unit
conversion_factor
base_qty
barcode_scope
```

داخل `POSLine`، ويتم تمريرها لاحقًا إلى فاتورة البيع العادية.

### 2. منع fallback الخطر

تم منع النمط القديم:

```python
product_service.items(search=code, limit=10)
```

داخل scan path. إذا كان الإدخال scan-like أو كاميرا، فلا يتم اختيار أول نتيجة نصية عند فشل الباركود.

### 3. دعم المخزون بالوحدة الأساسية

التحقق من المخزون صار على أساس:

```text
qty × conversion_factor <= available_base_qty
```

وهذا يمنع خطأ بيع كرتون كأنه قطعة واحدة.

### 4. تفضيلات POS عبر settings_service

أضيف:

```text
alrajhi_client/features/pos/pos_preferences.py
```

وتم إلغاء `QSettings` المباشر من:

```text
alrajhi_client/views/widgets/pos_widget.py
```

الحفظ الآن scoped حسب:

```text
user
branch
active settings profile
pos identity
```

### 5. POS Settings Contract

أضيف داخل:

```text
alrajhi_client/core/services/settings_service.py
```

العقد:

```python
get_pos_settings()
```

ويشمل:

```text
use_shifts
ui_language
print_language
quantity_decimals
price_decimals
stock policy
default warehouse
default cashbox
default payment method
touch density
barcode scanner settings
receipt paper
settings profile id
```

### 6. Touch density

أضيفت كثافات واجهة POS:

```text
compact
comfortable
touch
```

مع حفظ اختيار المستخدم عبر `POSPreferences`.

### 7. POS Permission

أضيفت صلاحية:

```text
ACTION_USE_POS
```

ومقابلها في RBAC:

```text
pos.use
```

### 8. i18n

أضيفت مفاتيح ترجمة جديدة للغات:

```text
ar
de
en
```

للكثافة، أخطاء الباركود، المخزون، وسلوك checkout.

## الفحوص

تم تشغيل:

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
python tools/phase171_material_document_guard.py
python tools/phase172_unit_barcode_api_guard.py
python tools/phase173_material_workspace_guard.py
python tools/phase174_material_security_guard.py
python tools/phase175_pos_touch_guard.py
```

كلها نجحت.

## ملاحظات

هذه المرحلة لم تحول POS إلى `TransactionDocumentTab` بالكامل بعد. القرار متعمد: تم أولًا توحيد الخدمة والسلوك والباركود والوحدات والإعدادات والصلاحيات. المرحلة التالية يمكن أن تعيد بناء واجهة POS بصريًا فوق نفس grid engine أو تنقل المطعم إلى نفس خط الباركود/الوحدات.
