# GATEWAY_PHASE_34_ADVANCED_TEST_REPORT

## الهدف
اختبار متقدم يحاكي تشغيل عدة أيام على نسخة Phase 34، مع تنفيذ سيناريو عملي شامل وفحص توافق طبقات الواجهة/الخدمات/Gateway/REST/SQLite.

## بيئة الاختبار
- وضع التشغيل: Local Mode Headless
- قاعدة اختبار مستقلة: `ALRAJHI_DB_PATH=/tmp/alrajhi_advanced_test_runtime/alrajhi_advanced_test.db`
- PyQt: تم استخدام fallback stubs للاختبار غير الرسومي لأن بيئة الاختبار لا تحتوي PyQt5.
- الاختبار الرسومي الكامل للواجهة لم يُشغل داخل هذه البيئة، لكن تم فحص توافق استدعاءات الواجهة للخدمات Static AST.

## الفحوصات المنفذة
1. `python3 -m compileall -q alrajhi_client alrajhi_server tools`
2. `python3 tools/architecture_guard.py`
3. استيراد جميع خدمات `core/services`.
4. إنشاء جميع Gateway factories والتحقق من `is_remote()`.
5. فحص عدم وجود وصول مباشر من `views` و `core/services` إلى DAO/Repository/SQLite.
6. فحص توافق استدعاءات الواجهة مع أسماء Methods الموجودة في الخدمات.
7. فحص توافق Remote Gateways مع `RestClient`.
8. تنفيذ سيناريو عملي متعدد الأيام:
   - إنشاء عميل.
   - إنشاء مورد.
   - إنشاء تصنيف.
   - إنشاء صنف.
   - إنشاء فاتورة شراء.
   - إنشاء فاتورة بيع.
   - إنشاء مرتجع بيع.
   - إنشاء مرتجع شراء.
   - إنشاء تحويل مستودعي.
   - إلغاء التحويل المستودعي.
   - محاولة تعديل فاتورة مرتبطة بمرتجع.
   - محاولة حذف فاتورة مرتبطة بمرتجع.
   - فحص Inventory Movements.
   - فحص Warehouse Movements.
   - فحص Inventory Ledger.
   - فحص Dual Read / Readiness / Controlled Read.
9. اختبار Offline Queue:
   - إنشاء طلب Offline.
   - تسجيل محاولة فاشلة.
   - تعليم خطأ 400 كـ failed.
   - التأكد من عدم بقائه pending.

## نتيجة السيناريو العملي
السيناريو النهائي بعد الإصلاحات أعطى:

```text
شراء: +20
بيع: -5
مرتجع بيع: +1
مرتجع شراء: -2
تحويل: -3 من المستودع 1، +3 إلى المستودع 2
إلغاء التحويل: +3 إلى المستودع 1، -3 من المستودع 2
```

النتيجة المتوقعة والفعليّة:

```text
رصيد الصنف التشغيلي = 14
رصيد Ledger للصنف = 14
فرق Dual Read = 0
رصيد المستودع الرئيسي التشغيلي = 14
رصيد Ledger للمستودع الرئيسي = 14
فرق Warehouse Dual Read = 0
```

## أخطاء اكتشفها الاختبار وتم إصلاحها

### 1. نقص `is_remote()` في بعض Gateway adapters
بعض الـ Local/Remote adapters لم تكن تملك `is_remote()` رغم أن الخدمات تعتمد عليها.

تم الإصلاح في:

```text
LocalCustomerGateway
LocalSupplierGateway
LocalCategoryGateway
LocalBranchGateway
LocalCashboxGateway
LocalOfflineQueueGateway
LocalCurrencyGateway
RemoteCustomerGateway
RemoteSupplierGateway
RemoteCategoryGateway
RemoteBranchGateway
RemoteCashboxGateway
RemoteCurrencyGateway
```

### 2. فشل استيراد `barcode_label_service` عند غياب python-barcode
كان الاستيراد يفشل مباشرة إذا لم تكن حزمة `python-barcode` مثبتة.

تم تحويلها إلى dependency اختيارية، بحيث لا يفشل تشغيل المشروع كله، ويظهر خطأ واضح فقط عند استخدام طباعة صورة الباركود.

### 3. نقص دوال Ledger للتحويلات المستودعية
`WarehouseService.create_transfer()` كان يستدعي:

```text
_record_transfer_ledger_entries
_record_transfer_cancel_ledger_entries
```

لكن الدوال غير موجودة.

تمت إضافتها مع:

```text
_direction_from_quantity
_record_warehouse_ledger_entry
```

### 4. السماح بتعديل/حذف فاتورة مرتبطة بمرتجع
الاختبار كشف أن فاتورة بيع عليها مرتجع كان يمكن حذفها، وهذا يسبب رصيداً خاطئاً.

تمت إضافة Guard في العميل والخادم:

```text
لا يمكن تعديل فاتورة مرتبطة بمرتجعات.
لا يمكن حذف فاتورة مرتبطة بمرتجعات.
```

### 5. `purchase_return` لم يكن محسوباً في رصيد الصنف
`items.quantity` كان لا يطرح `purchase_return`.

تم إصلاح حساب الرصيد ليشمل:

```text
sales_return = دخول
purchase_return = خروج
```

### 6. ترحيل المستودع كان يضاعف الرصيد عند إنشاء Warehouse Balance متأخر
عند إنشاء أول حركة مستودعية بعد فاتورة شراء، كان `bootstrap_defaults()` يرحّل `items.quantity` كـ `migration_opening` ثم تسجل الفاتورة نفسها، فيحدث double-count.

تم الإصلاح: إذا كان للصنف `inventory_movements` موجودة، لا يتم ترحيل `items.quantity` كرصيد افتتاحي للمستودع.

### 7. Integrity Check كان يعتبر التحويل المستودعي تكراراً خاطئاً
كان `duplicate_source_rows` يعتبر أكثر من Ledger row لنفس `source_id` مشكلة، مع أن التحويل الطبيعي له سطر خروج وسطر دخول.

تم تعديل الفحص ليعتبر التكرار فقط عند تطابق:

```text
source_table
source_id
item_id
warehouse_id
movement_type
direction
```

## النتيجة النهائية

```text
compileall: PASS
architecture_guard: PASS
core services import: PASS
all gateway factories: PASS
UI → Service command compatibility: PASS
Remote Gateway → RestClient compatibility: PASS
advanced multi-day business flow: PASS
Offline Queue permanent failure handling: PASS
Dual Read stock difference: 0
Readiness blockers: none in the tested scenario
```

## حدود الاختبار
- لم يتم تشغيل واجهة PyQt5 فعلياً بسبب غياب PyQt5 في بيئة الاختبار.
- لم يتم تشغيل Flask server حياً مع HTTP حقيقي في هذه البيئة.
- تم فحص توافق REST بشكل static بين Remote Gateways و RestClient، وليس عبر شبكة فعلية.

## التوصية
هذه النسخة أصلح من Phase 34 الأصلية. يجب اعتماد هذه النسخة للاختبار الميداني بدلاً من Phase 34 السابقة، ثم تشغيلها على:

```text
Server + Client 1 + Client 2
```

مع تنفيذ نفس السيناريو عملياً من الواجهة.
