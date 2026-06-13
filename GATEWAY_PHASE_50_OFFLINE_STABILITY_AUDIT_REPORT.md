# Phase 50 - Offline Stability Audit

## الهدف
فحص المشاكل المشابهة لانهيار التطبيق عند انقطاع الخادم أثناء عمليات الحفظ أو بعد الحفظ، خصوصاً عندما تنفذ الواجهة قراءات REST لا يمكن إدخالها في Offline Queue.

## الإصلاحات
- إضافة `offline_read.py` كأداة مركزية لاكتشاف أخطاء القراءة أثناء عدم الاتصال.
- تركيب `install_offline_exception_hook(app)` في `main.py` لمنع أخطاء القراءة غير المتوقعة من إسقاط التطبيق.
- حماية تحديث مرتجعات المبيعات عند انقطاع الخادم.
- حماية تحديث مرتجعات المشتريات عند انقطاع الخادم.
- حماية تحميل فواتير المرتجعات عند انقطاع الخادم.
- حماية تحديث السندات عند انقطاع الخادم.
- حماية تحميل العملاء/الموردين داخل نافذة السندات عند انقطاع الخادم.
- حماية تحديث المستخدمين عند انقطاع الخادم.
- حماية تحميل الفروع داخل نافذة المستخدمين عند انقطاع الخادم.
- حماية تحديث سجل التدقيق عند انقطاع الخادم.
- إضافة `tools/offline_ui_guard.py` لمنع رجوع هذه المسارات إلى سلوك غير محمي.

## نطاق الفحص
تم فحص المسارات التالية لأنها شبيهة بمشكلة `/api/invoices` و `/api/exchange_rates`:

- invoices list refresh
- invoice next reference
- currency rates
- returns list refresh
- returns invoice loading
- vouchers list refresh
- voucher party loading
- users list refresh
- branches loading
- audit log refresh
- global PyQt signal exception handling

## النتيجة
عند انقطاع الخادم، يجب أن تكون النتيجة الآن:

- لا Crash.
- لا Aborted.
- تظهر رسالة تحذير فقط.
- عمليات الحفظ القابلة للـ Queue تبقى في Offline Queue.
- قراءات الجداول تفشل بهدوء وتُترك البيانات السابقة كما هي.

## الفحوصات
- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
- offline_read_guard: PASS
- offline_ui_guard: PASS
- zip test: PASS
