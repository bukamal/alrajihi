# Phase 54 - Manufacturing Cost Numeric Hotfix

## الهدف
إصلاح انهيار شاشة تفاصيل أمر الإنتاج عند تسجيل استهلاك/إتمام الإنتاج بسبب مقارنة قيم كلفة واردة كنصوص مع أرقام.

## السبب
`average_cost` و `purchase_price` قد تصل من SQLite/REST كنصوص، بينما الكود كان ينفذ مقارنة مباشرة:

```python
it.get('average_cost', 0) > 0
```

وهذا يسبب:

```text
TypeError: '>' not supported between instances of 'str' and 'int'
```

## الإصلاح
تم تحويل القيم إلى أرقام آمنة عبر `_num()` قبل المقارنة والحساب:

```python
average_cost = _num(it.get('average_cost'), 0)
purchase_price = _num(it.get('purchase_price'), 0)
price = average_cost if average_cost > 0 else purchase_price
```

كما تم ضمان تحويل قيمة العرض قبل تمريرها إلى `QDoubleSpinBox`.

## الحماية المضافة
أُضيف فحص:

```text
tools/manufacturing_numeric_guard.py
```

لمنع تكرار المقارنة الرقمية المباشرة على قيم `.get()` الخام داخل شاشات التصنيع.

## الفحوصات

```text
compileall: PASS
architecture_guard: PASS
reports_contract_check: PASS
phase32_invoice_flow_guard: PASS
offline_read_guard: PASS
offline_widget_guard: PASS
form_validation_guard: PASS
manufacturing_ui_guard: PASS
manufacturing_numeric_guard: PASS
```
