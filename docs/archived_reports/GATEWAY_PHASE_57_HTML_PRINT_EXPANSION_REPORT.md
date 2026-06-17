# Phase 57 — HTML Print Expansion

## الهدف
توسيع طباعة HTML الموحدة بعد الفواتير لتغطي السندات، المرتجعات، التقارير، وأوامر الإنتاج، مع إبقاء تجربة المستخدم من زر الطباعة نفسه عبر قائمة خيارات.

## ما أضيف
- `production_order_html()` لقالب أمر الإنتاج.
- خيارات HTML/طباعة/PDF للسندات.
- خيارات HTML/طباعة/PDF للمرتجعات.
- خيارات HTML/طباعة/PDF للتقارير.
- زر طباعة داخل تفاصيل أمر الإنتاج.
- Guard جديد: `tools/html_print_expansion_guard.py`.

## القوالب الموحدة
تستخدم جميعها رأس الشركة والتذييل وإعدادات الطباعة نفسها:
- اسم الشركة
- الشعار
- العنوان
- الهاتف
- البريد
- الرقم الضريبي
- اللون والخط
- قالب A4 أو حراري

## الفحوصات
- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
- offline_read_guard: PASS
- offline_widget_guard: PASS
- form_validation_guard: PASS
- manufacturing_numeric_guard: PASS
- manufacturing_ui_guard: PASS
- manufacturing_flow_guard: PASS
- html_print_expansion_guard: PASS
