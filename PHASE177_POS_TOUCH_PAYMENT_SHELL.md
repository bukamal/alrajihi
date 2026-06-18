# Phase 177 — POS Touch Payment Shell

## الهدف

فصل واجهة الدفع والملخص وأزرار البيع السريع عن `POSWidget` وتحويلها إلى مكوّن لمس مستقل، مع الحفاظ على منطق POS الموجود في `POSService` وعدم كسر خط الباركود/الوحدات/المخزون الذي تم ضبطه في المراحل السابقة.

## التغييرات

### 1. مكوّن جديد

تمت إضافة:

```text
alrajhi_client/features/pos/pos_payment_shell.py
```

ويحتوي على:

```text
POSPaymentShell
```

المكوّن مسؤول عن العرض فقط:

```text
إجمالي السلة
الباقي / الراجع
طريقة الدفع
المدفوع
أزرار نقدًا/بطاقة/تعليق/استرجاع/حذف/تفريغ/إنهاء البيع
كثافة لمس compact / comfortable / touch
```

ولا يقوم بأي حفظ أو طباعة أو تسجيل صندوق أو اتصال API مباشر.

### 2. تنظيف `POSWidget`

تم تعديل:

```text
alrajhi_client/views/widgets/pos_widget.py
```

وإزالة الصفوف القديمة المدمجة:

```text
summary_row
buttons
```

واستبدالها بـ:

```text
self.payment_shell = POSPaymentShell(self, self)
```

مع aliases متوافقة مع الكود القديم:

```text
total_label
change_label
payment_combo
paid_spin
cash_btn
card_btn
suspend_btn
resume_btn
remove_btn
clear_btn
checkout_btn
```

حتى لا ينكسر workflow الحالي.

### 3. Touch density

`POSPaymentShell` يدعم:

```text
apply_density(density)
```

ويغير ارتفاع الأزرار، حقول الدفع، وحجم خطوط الإجمالي حسب الكثافة.

### 4. i18n

أضيفت مفاتيح ترجمة باللغات الثلاث:

```text
pos_payment_shell_title
pos_total_card
pos_change_card
pos_payment_shell_unified
```

داخل:

```text
alrajhi_client/i18n/translator.py
```

### 5. Guard

أضيف:

```text
tools/phase177_pos_payment_shell_guard.py
```

ويتحقق من:

```text
POSWidget يستخدم POSPaymentShell
إزالة summary_row/buttons القديمة
وجود payment combo وال paid spin داخل المكوّن الجديد
وجود apply_density
وجود مفاتيح الترجمة
```

## الفحوص

تم تشغيل:

```text
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase176_pos_visual_grid_guard.py
python tools/phase177_pos_payment_shell_guard.py
```

كما تم تشغيل guards المراحل 169 إلى 175 بنجاح. عند تشغيل كل guards دفعة واحدة في أمر واحد حدث timeout بيئي بعد نجاح Phase 176، لكن Phase 177 guard نجح عند تشغيله منفردًا.

## النتيجة

واجهة POS أصبحت أقرب إلى shell لمس منظم:

```text
Scan / Qty
POSLineGrid
POSPaymentShell
Status
```

مع بقاء منطق الباركود، الوحدات، المخزون، الصندوق، والشفتات في الخدمات الأصلية للمشروع.
