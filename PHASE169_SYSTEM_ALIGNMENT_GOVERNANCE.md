# Phase 169 — System Alignment & Governance

## هدف المرحلة

تثبيت طبقة `features/transactions` الجديدة ضمن أنظمة المشروع الأصلية بدل أن تصبح نظامًا موازيًا. هذه المرحلة توقف التوسع الشكلي مؤقتًا وتفرض احترام:

- نظام الترجمة العربي/الألماني/الإنجليزي.
- مصطلح المشروع الرسمي للـ `item`: **المادة / المواد**.
- نظام الإعدادات المركزي `settings_service` وملفات الإعدادات النشطة.
- تعدد المستخدمين والفروع وSettings Profiles في حفظ تفضيلات الجداول.
- نظام الباركود المركزي ومنع fallback الخطر الذي يضيف أول نتيجة بحث عند فشل قراءة الباركود.
- منع وصول واجهات `transactions` إلى قواعد البيانات أو REST مباشرة.

## ما تغير

### 1. Localization helper

أضيف:

```text
alrajhi_client/features/transactions/i18n.py
```

ويجب أن تمر كل نصوص الواجهة داخل `features/transactions` عبر:

```python
tr("translation_key")
html_bold("translation_key")
```

### 2. Transaction terminology

تم نقل عناوين الأعمدة والمستندات والـ presets إلى مفاتيح ترجمة بدل نصوص مباشرة.

الأهم:

```text
item => المادة / Item / Artikel
```

ولم يعد عنوان العمود العربي هو `الصنف`.

### 3. Transaction settings contract

أضيف داخل:

```text
alrajhi_client/core/services/settings_service.py
```

method جديد:

```python
get_transaction_settings(document_type)
```

ويرجع عقد إعدادات موحدًا يشمل:

- لغة الواجهة والطباعة.
- منازل الكمية والسعر.
- طريقة التقريب.
- سياسة المخزون السالب والتحذير.
- المستودع الافتراضي.
- طريقة الدفع الافتراضية.
- preset الجداول الافتراضي.
- إعدادات الباركود scanner prefix/suffix/min length.
- قالب الطباعة.
- settings profile النشط.

### 4. Per-user / per-branch / per-profile grid preferences

تمت إعادة كتابة:

```text
alrajhi_client/features/transactions/grids/transaction_grid_preferences.py
```

لم يعد يستخدم `QSettings` مباشرة.

الحفظ الآن عبر `settings_service` وبمفتاح scoped:

```text
transactions/users/{user}/branches/{branch}/profiles/{profile}/{document_type}/...
```

وهذا يمنع تداخل ترتيب الأعمدة بين المستخدمين أو الفروع أو profiles.

### 5. Feature flags via settings_service

تم تعديل:

```text
alrajhi_client/features/transactions/feature_flags.py
```

ليقرأ flags من `settings_service` بدل `QSettings` المباشر.

### 6. Barcode input safety foundation

أضيف:

```text
alrajhi_client/core/services/barcode_input_service.py
```

السلوك الجديد:

- scan-like input يبحث exact barcode فقط.
- إذا لم يوجد الباركود لا يضيف أي مادة.
- لا يوجد fallback إلى `catalog_service.items(... limit=1)` بعد فشل الباركود.
- manual search لا يضيف المادة إلا إذا وجد نتيجة وحيدة واضحة.
- إذا تعددت نتائج البحث يعرض رسالة ambiguity ولا يختار أول نتيجة.

تم تعديل:

```text
alrajhi_client/features/transactions/transaction_document_tab.py
```

ليستخدم:

```python
barcode_input_service.lookup_entry(text, mode="auto")
```

بدل الخلط السابق بين قراءة الباركود والبحث النصي.

### 7. Governance guard

أضيف:

```text
tools/phase169_system_governance_guard.py
```

ويفحص:

- منع `QSettings` import داخل `features/transactions`.
- منع imports منخفضة المستوى مثل `database`, `requests`, `connection_rest`.
- منع barcode fallback الخطر.
- منع نصوص واجهة مباشرة داخل `QLabel`, `QPushButton`, `setText`, `setPlaceholderText`, `setToolTip` إلا عبر `tr()/translate()/html_bold()` أو قيم رقمية/ديناميكية.

## الفحوص المنفذة

```text
python -m compileall -q alrajhi_client
python tools/phase169_system_governance_guard.py
```

النتيجة: ناجحة.

## حدود المرحلة

هذه المرحلة لا تضيف endpoint جديد للـ API بعد. تم إصلاح مسار واجهة `TransactionDocumentTab` ومنع fallback الخطر. المرحلة التالية يجب أن تضيف endpoint دقيق للباركود في remote API مثل:

```text
GET /api/items/by-barcode/<barcode>
```

أو:

```text
GET /api/items?barcode=<barcode>&exact=true
```

ثم تعديل `RemoteItemGateway.get_by_barcode()` لاستخدامه بدل الجلب الواسع.

## القرار المعماري

قبل POS/Restaurant يجب تنفيذ المرحلة التالية:

```text
Phase 170 — Remote Barcode API Exact Lookup
```

ثم:

```text
Phase 171 — Transaction Security / RBAC Enforcement
```
