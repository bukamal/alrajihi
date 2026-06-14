# Phase 99 – Barcode HTML/PNG Label Rendering

## الهدف
توحيد طباعة الباركود المفرد والمتعدد بحيث يتم توليد الملصق أولًا كـ HTML أو PNG، ثم طباعته/حفظه من مسار موحد. هذا يقلل اختلافات الطابعات ويضمن ظهور العربية والألمانية والإنجليزية والشعار وQR والباركود بنفس الشكل.

## التعديلات

### 1. خدمة ملصقات الباركود
تم تحديث:
`alrajhi_client/core/services/barcode_label_service.py`

أصبحت الخدمة تدعم:
- HTML موحد للملصقات.
- اتجاه اللغة تلقائيًا:
  - العربية RTL.
  - الألمانية/الإنجليزية LTR.
- شعار الشركة من الإعدادات كـ Data URI.
- QR اختياري مبني على قيمة الباركود.
- صورة الباركود كـ PNG Base64.
- اختيار اسم المادة حسب اللغة مستقبلًا إذا توفرت الحقول:
  - `name_ar`
  - `name_de`
  - `name_en`
  - fallback إلى `name` الحالي.

### 2. نظام الطباعة الموحد
تم تحديث:
`alrajhi_client/printing/printing_service.py`

أضيف:
- `save_html_png(...)`
- `barcode_labels_png(...)`

وبذلك أصبح المسار:

```text
بيانات المواد → HTML موحد → PDF أو PNG أو طباعة Qt
```

### 3. نافذة طباعة الباركود
تم تحديث:
`alrajhi_client/views/dialogs/batch_print_dialog.py`

أصبحت الطباعة تستخدم:
- PDF من نفس HTML.
- PNG من نفس HTML.
- طابعة نظام Qt من نفس HTML.

وتم إيقاف المسار القديم الذي يرسل نصًا خامًا للطابعة؛ لأنه لا يضمن العربية والشعار وQR بشكل ثابت.

### 4. إعدادات الطباعة
تم تحديث:
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/i18n/translator.py`

أضيفت إعدادات:
- إظهار الشعار على لصاقة الباركود.
- إظهار QR على لصاقة الباركود.

مع ترجمة عربية/ألمانية/إنجليزية.

## الاختبارات
نجح:
- `tools/verify_phase99_barcode_html_png_labels.py`
- `compileall`

## ملاحظة تشغيلية
للطابعات الحرارية التي لا تدعم العربية جيدًا، المسار المفضل الآن هو طباعة PNG/PDF أو طابعة نظام Qt، لا إرسال نص خام ESC/POS.
