# Phase 106 — Invoice edit price-warning deep test

## Scope
فحص مسار فتح فاتورة محفوظة للتعديل ورسالة: تغيرت أسعار بعض المواد منذ إنشاء الفاتورة.

## Defect found
المقارنة السابقة كانت تقارن:

- سعر السطر المحفوظ: سعر وحدة الفاتورة المختارة، مثل كرتون = 12 قطعة.
- السعر الحالي للمادة: سعر الوحدة الأساسية فقط، مثل قطعة واحدة.

لذلك في حالة:

- سعر القطعة = 10
- الكرتون = 12 قطعة
- سعر السطر المحفوظ = 120

النظام كان يرى فرقًا خاطئًا بين 120 و10، رغم أن السعر لم يتغير فعليًا.

كما أن الفحص كان يُنفّذ قبل تحميل السطور في `lines_model`، ولذلك عند اختيار تحديث الأسعار لا يتم تطبيق التحديث على السطور المعروضة.

## Fix
تم تعديل `alrajhi_client/views/dialogs/invoice_dialog.py`:

1. نقل `check_price_differences(inv)` بعد `self.lines_model.load_invoice_lines(...)`.
2. إضافة helper موحّد:
   - `_line_conversion_factor`
   - `_item_current_unit_price_usd`
3. مقارنة السعر الحالي بعد ضرب سعر المادة الأساسي بمعامل وحدة سطر الفاتورة:

`current_unit_price = current_base_item_price * invoice_line_conversion_factor`

4. عند قبول تحديث الأسعار، يتم تحديث سعر السطر إلى سعر الوحدة المختارة، وليس سعر الوحدة الأساسية.

## Deep regression cases

### Sale invoice / box unit / no real price change
- Base selling price: 10
- Invoice unit factor: 12
- Saved line unit price: 120
- Expected: no warning
- Result: PASS

### Sale invoice / box unit / real price change
- Old base selling price: 10
- New base selling price: 11
- Invoice unit factor: 12
- Expected new line price: 132
- Result: PASS

### Purchase invoice / decimal price
- Base purchase price: 4.25
- Unit factor: 5
- Expected current unit price: 21.25
- Result: PASS

### Invalid factor fallback
- Base price: 9.5
- Factor: 0
- Expected fallback current price: 9.5
- Result: PASS

## Executed tests

- `python -m compileall -q alrajhi_client alrajhi_server tools`
- `python tools/phase32_invoice_flow_guard.py`
- `python tools/invoice_units_guard.py`
- `python tools/vouchers_deep_accounting_test_phase105.py`
- `python tools/invoice_price_edit_deep_test_phase106.py`

All passed.

## Remaining limitation
لم يتم تشغيل واجهة PyQt فعليًا داخل بيئة الفحص لأن PyQt5 غير مثبت في الحاوية. تم اختبار الحساب والمنطق المصدرّي الذي تسبب في الرسالة الخاطئة، مع حراس تمنع رجوع المقارنة القديمة.
