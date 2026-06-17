# Phase 37 — Pre-Redesign Stabilization

## الهدف
تثبيت صفحات التقارير والمراقبة قبل البدء في إعادة تصميم لوحة التحكم والتنقل.

## التعديلات
- جعل `ReportsWidget.refresh_report()` يحدّث التبويب الحالي فقط بدلاً من تحميل كل التقارير عند فتح الصفحة.
- إضافة تحديث كسول عند تغيير تبويب التقارير عبر `currentChanged`.
- إضافة `refresh_all_reports()` كأداة اختبار/تشخيص لاستخدام المطورين.
- إضافة `tools/reports_contract_check.py` لفحص:
  - عدم وجود استدعاءات ناقصة داخل `ReportsWidget`.
  - توافق استدعاءات `reporting_service`, `inventory_service`, `offline_queue_service`, `product_service` مع الدوال الموجودة فعلاً.
  - وجود جداول تقارير Phase 36 داخل الواجهة.
- ربط فحص التقارير في GitHub workflow بجانب `architecture_guard` و `phase32_invoice_flow_guard`.

## سبب التعديل
الخطأ السابق:

```text
'ReportsWidget' object has no attribute '_refresh_phase36_reports'
```

كشف أن توسيعات التقارير تحتاج فحص عقد واجهة/خدمة دائم. Phase 37 يمنع رجوع هذا النوع من الأخطاء قبل البدء في تصميم الواجهة الجديدة.

## الفحوصات
- `python3 -m compileall -q alrajhi_client alrajhi_server`: ناجح
- `python3 tools/architecture_guard.py`: ناجح
- `python3 tools/phase32_invoice_flow_guard.py`: ناجح
- `python3 tools/reports_contract_check.py`: ناجح

## ملاحظات
لم يتم تغيير منطق التقارير المالي أو المخزني. التعديل يخص الاستقرار، التحميل الكسول، وفحص التوافق.
