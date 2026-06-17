# Phase 36 Reports Hotfix

## سبب الإصلاح
عند فتح تبويب التقارير ظهرت الرسالة:

`ReportsWidget object has no attribute _refresh_phase36_reports`

السبب أن Phase 36 أضاف استدعاء `self._refresh_phase36_reports(...)` داخل `refresh_report()`، لكن دالة التحديث لم تكن موجودة داخل `ReportsWidget`.

## ما تم إصلاحه
- إضافة `ReportsWidget._refresh_phase36_reports()` داخل الكلاس.
- إضافة `ReportsWidget._rows_from()` لتوحيد أشكال استجابات التقارير من Local/API.
- جعل تقارير Phase 36 دفاعية: أي فشل في تقرير تشخيصي لا يمنع فتح صفحة التقارير.
- إضافة دعم الطباعة للتبويبات الجديدة:
  - ميزان المراجعة
  - كشف حساب عميل
  - كشف حساب مورد
  - أرصدة العملاء
  - أرصدة الموردين
  - أعمار ديون العملاء
  - أعمار ديون الموردين
  - مطابقة Ledger
  - Dual Read
  - جاهزية Ledger
  - Offline Queue
  - فحص الوحدات

## الفحوصات
- `compileall`: ناجح
- `architecture_guard`: ناجح
- AST method check: ناجح
- تأكد أن كل استدعاءات `_refresh_*` داخل `refresh_report()` لها دوال مقابلة: ناجح

## ملاحظة
هذا الإصلاح لا يغير منطق الحسابات أو الأرصدة. هو إصلاح تحميل/عرض لتبويب التقارير وتوافق الطباعة.
