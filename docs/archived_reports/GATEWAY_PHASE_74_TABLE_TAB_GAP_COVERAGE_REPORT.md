# GATEWAY PHASE 74 – Table/Tab Gap Coverage Hotfix

## الهدف
معالجة الفجوات المتبقية بعد Phase 73، حيث بقيت بعض النوافذ والجداول خارج التغطية المرئية بسبب أنماط محلية أو عدم استدعاء طبقة `modern_ui`.

## المبدأ
تم الحفاظ على الأسلوب الآمن:
- لا يوجد EventFilter عام.
- لا يوجد Runtime Polish شامل.
- لا توجد إعدادات QtWebEngine أو Chromium.
- لا تعديل جذري في سلوك النوافذ.
- التغطية تتم عبر QSS مركزي ونداءات انتقائية داخل النوافذ المتأثرة.

## النوافذ التي أضيفت لها التغطية
- `alrajhi_client/views/widgets/invoices_widget.py`
  - فواتير البيع.
  - فواتير الشراء.
  - التبويبات والجداول الداخلية.

- `alrajhi_client/views/widgets/monitoring_widget.py`
  - جدول مراقبة التشغيل.
  - صندوق الملخص.

- `alrajhi_client/views/widgets/offline_queue_widget.py`
  - جدول الطلبات المعلقة.
  - صندوق المعلومات.

- `alrajhi_client/views/widgets/pos_widget.py`
  - جدول نقطة البيع.
  - ألوان الإجمالي والباقي من Design System.

- `alrajhi_client/views/dialogs/production_details_dialog.py`
  - تبويبات تفاصيل أمر الإنتاج.
  - جداول المواد المستهلكة والمنتج النهائي والحجوزات.

## تحسينات مساعدة
- توسيع `modern_ui.py` لإضافة صناديق معلومات موحدة:
  - `ModernInfoBox`
  - `ModernSummaryBox`

- تحديث مؤشرات الحالة في الإعدادات لاستخدام ألوان Design System بدل ألوان hard-coded.

## Guard جديد
تمت إضافة:
`tools/verify_window_table_tab_coverage.py`

وظيفته:
- البحث عن الملفات التي تحتوي `QTableWidget/QTableView/QTreeWidget/QTreeView/QTabWidget`.
- التأكد من وجود تغطية Design System آمنة عبر:
  - `apply_modern_widget`
  - `apply_modern_dialog`
  - أو نمط Modern مخصص معتمد مثل `apply_modern_item_style` و `_apply_modern_invoice_style`.

## الاختبارات
- `python3 -m compileall -q alrajhi_client` ✅
- `python3 tools/verify_window_table_tab_coverage.py` ✅

## ملاحظة
هذه المرحلة لا تعد بإزالة كل لون محلي من كامل المشروع، لكنها تغلق الفجوات المباشرة في النوافذ التي تحتوي جداول/تبويبات ولم تكن مغطاة في Phase 73.
