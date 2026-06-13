# Phase 56 - HTML Print Foundation

## الهدف
إضافة أساس طباعة HTML موحد يفتح في المتصفح، مع الإبقاء على مسار الطباعة الحالي، واعتماد بيانات الشركة من الإعدادات.

## ما تم تطبيقه
- إضافة `PrintingService.open_html_in_browser()` لفتح HTML في المتصفح الافتراضي.
- إضافة `PrintingService.invoice_browser_preview()`.
- تحويل زر الطباعة في نافذة الفاتورة إلى قائمة خيارات موحدة:
  - معاينة داخل البرنامج.
  - معاينة HTML في المتصفح.
  - طباعة مباشرة.
  - تصدير PDF.
- فصل بناء بيانات الطباعة داخل `InvoiceDialog` في دالة واحدة `_build_invoice_print_payload()`.
- الحفاظ على قوالب الطباعة الموحدة الموجودة في `printing/print_templates.py` والتي تعتمد على:
  - معلومات الشركة.
  - الشعار.
  - الرقم الضريبي.
  - إعدادات الطباعة.
  - RTL عربي.
  - A4 / Thermal.

## الفحوصات
- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
- offline_read_guard: PASS
- offline_widget_guard: PASS

## ملاحظات
هذه المرحلة تطبق الأساس على الفواتير أولاً. التوسيع الطبيعي التالي هو تطبيق نفس القائمة الموحدة على السندات، المرتجعات، التقارير، وأوامر الإنتاج.
