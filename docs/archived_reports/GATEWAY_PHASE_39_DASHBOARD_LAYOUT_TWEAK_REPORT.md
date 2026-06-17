# Phase 39 - Dashboard Layout Tweak

## الهدف
تعديل تخطيط لوحة التحكم وفق الطلب:

- نقل شريط التنبيهات إلى مكان شريط آخر الحركات.
- حذف شريط آخر الحركات نهائياً.
- جعل شريط التنبيهات صغير الارتفاع.
- وضع بطاقة جديدة في مكان شريط التنبيهات السابق تحتوي على:
  - اسم المشروع.
  - شعار بصري داخلي.
  - رصيد الصندوق.
  - حركة البيع اليومية.
  - حركة الشراء اليومية.
  - صافي الحركة اليومية.

## الملفات المعدلة

- `alrajhi_client/views/widgets/dashboard_widget.py`

## التعديلات

- استبدال `recent_panel` بـ `alerts_panel` في الصف السفلي.
- حذف `_create_recent_panel()` و `_refresh_recent()`.
- إضافة `_create_project_panel()`.
- إضافة `_refresh_project_card()`.
- تحديث `refresh_all()` ليحدث بطاقة المشروع بدلاً من آخر الحركات.
- ضبط ارتفاع التنبيهات إلى نطاق صغير.

## الفحوصات

- `compileall`: PASS
- `architecture_guard`: PASS
- `reports_contract_check`: PASS
- `phase32_invoice_flow_guard`: PASS

## ملاحظة

لم يتم تغيير أي منطق أعمال أو API. التعديل UI layout فقط.
