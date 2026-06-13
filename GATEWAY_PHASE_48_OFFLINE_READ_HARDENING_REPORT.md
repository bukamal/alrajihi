# Phase 48 — Offline Read Hardening

## الهدف
فحص وإصلاح المشاكل المشابهة لمشكلة `/api/exchange_rates` التي ظهرت عند حفظ فاتورة من عميل متصل بخادم ثم توقف الخادم قبل الحفظ.

## المشكلة الأصلية
كان مسار الحفظ يستخدم قراءة REST غير قابلة للـ Offline Queue أثناء عملية كتابة قابلة للانتظار، فتنهار العملية قبل إضافة الفاتورة إلى الطابور.

## الإصلاحات المطبقة

### 1. أرقام الفواتير أثناء Offline
- `InvoiceService.next_reference()` أصبح يولد مرجعاً مؤقتاً عند فشل جلب `/api/invoices/next-reference`.
- أمثلة:
  - `SOFF-YYYYMMDD-HHMMSS` للمبيعات.
  - `POFF-YYYYMMDD-HHMMSS` للمشتريات.

### 2. فحص تكرار مرجع الفاتورة
- `InvoiceService.reference_exists()` لم يعد يسقط الحفظ عند فشل قراءة قائمة الفواتير.
- عند Offline يتجاوز الفحص المحلي ويترك الحسم النهائي للخادم عند المزامنة.

### 3. فحص رصيد المخزون قبل حفظ فاتورة بيع
- `InvoiceDialog._stock_available_for_item()` لم يعد يسقط الحفظ إذا فشل جلب المادة من الخادم.
- في Offline يتم تخطي الفحص المحلي فقط، وتبقى صلاحية الخادم عند إعادة تشغيل الطابور هي الحاكمة.

### 4. المستودع الافتراضي والرصيد المتاح
- `WarehouseService.default_warehouse_id()` و `default_warehouse()` و `available_qty()` أصبحت تتحمل انقطاع الخادم وتعيد `None` بدلاً من إسقاط التطبيق.

### 5. POS وحركة الصندوق أثناء Offline
- إذا أعاد إنشاء فاتورة POS معرفاً سالباً يدل على أنها دخلت Offline Queue، لا يتم إرسال حركة صندوق مستقلة.
- السبب: الفاتورة المعلقة تحتوي بيانات الدفع، ويجب أن تُعالج ذرياً عند إعادة إرسالها للخادم.

### 6. فحص حماية جديد
أضيف:

```text
tools/offline_read_guard.py
```

يفحص وجود fallback في المسارات الحرجة:

```text
currency cache fallback
invoice reference fallback
invoice duplicate-reference fallback
invoice stock precheck fallback
warehouse default fallback
pos queued cash movement skip
```

## نتائج الفحص

```text
compileall: PASS
architecture_guard: PASS
reports_contract_check: PASS
phase32_invoice_flow_guard: PASS
offline_read_guard: PASS
zip test: PASS
```

## ملاحظة تشغيلية
هذه الإصلاحات لا تلغي ضرورة تحقق الخادم عند المزامنة. هي تمنع انهيار العميل فقط وتسمح للطلبات القابلة للانتظار أن تدخل Offline Queue بأمان.
