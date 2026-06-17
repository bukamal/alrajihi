# Phase 47 - Offline Currency Fallback Hotfix

## المشكلة
عند حفظ فاتورة شراء/بيع من عميل Remote بعد توقف الخادم، كان `InvoiceDialog` يحاول تحويل الأسعار عبر `currency.convert()`، ثم يقرأ أسعار الصرف من:

```text
GET /api/exchange_rates
```

وبما أن هذا طلب قراءة غير قابل للـ Offline Queue، كان ينتج:

```text
No connection and this operation cannot be queued safely: /api/exchange_rates
```

ثم يسقط التطبيق أثناء حفظ الفاتورة.

## الإصلاح
أضيف fallback آمن في نظام العملات:

- تخزين آخر أسعار صرف ناجحة داخل `QSettings`.
- استخدام آخر سعر محفوظ عند انقطاع الخادم.
- استخدام أسعار افتراضية آمنة إن لم يوجد Cache.
- منع RemoteCurrencyGateway من إسقاط التطبيق عند فشل `/api/exchange_rates`.
- إضافة fallback لإعدادات RemoteSettingsGateway عند انقطاع الخادم.

## السلوك الجديد
عند توقف الخادم:

```text
currency.convert()
```

لا يسقط التطبيق، بل يستخدم:

```text
آخر سعر صرف محفوظ
أو السعر الافتراضي المحلي
```

وبذلك يمكن للفواتير أن تتابع مسار الـ Offline Queue بدلاً من الانهيار.

## الملفات المعدلة

```text
alrajhi_client/currency.py
alrajhi_client/gateways/remote/currency_gateway.py
alrajhi_client/gateways/remote/settings_gateway.py
```

## التحقق

```text
compileall: PASS
architecture_guard: PASS
reports_contract_check: PASS
phase32_invoice_flow_guard: PASS
zip test: PASS
```

## ملاحظة
هذا الإصلاح لا يعدل سعر الصرف من لوحة التحكم. التعديل يبقى من الإعدادات فقط. بطاقة الصندوق والفواتير تقرأ آخر سعر متاح عند انقطاع الاتصال.
