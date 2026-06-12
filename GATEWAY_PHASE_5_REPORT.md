# Gateway Phase 5 Report — Invoice Gateway Wrapper

## الهدف
تحويل الفواتير إلى مسار Gateway موحد بدون إعادة تصميم منطق الحفظ أو التأثير المالي/المخزني.

## ما تم تنفيذه

### 1. إضافة عقد InvoiceGateway
تمت إضافة الملف:

- `alrajhi_client/gateways/invoice_gateway.py`

ويحتوي على العقد الموحد:

- `list(...)`
- `get(invoice_id)`
- `create(data)`
- `update(invoice_id, data)`
- `delete(invoice_id)`
- `next_reference(inv_type)`
- `has_linked_vouchers(invoice_id)`
- `is_remote()`

### 2. إضافة Local Adapter
تمت إضافة:

- `alrajhi_client/gateways/local/invoice_gateway.py`

وهو المكان الوحيد المسموح له حالياً باستخدام:

- `database.dao.invoice_dao`

### 3. إضافة Remote Adapter
تمت إضافة:

- `alrajhi_client/gateways/remote/invoice_gateway.py`

ويستخدم `RestClient` بدلاً من DAO.

### 4. تعديل InvoiceService
تم تعديل:

- `alrajhi_client/core/services/invoice_service.py`

ليصبح المسار:

```text
UI / POS / Widgets
→ InvoiceService
→ InvoiceGateway
→ Remote API أو Local DAO Adapter
```

بدلاً من:

```text
InvoiceService
→ invoice_dao مباشرة
```

### 5. تحسين توافق Remote Invoice Listing
تم تعديل:

- `alrajhi_client/database/connection_rest.py`
- `alrajhi_server/api/invoices.py`

لدعم تمرير فلاتر إضافية بشكل متوافق:

- `search`
- `customer_id`
- `supplier_id`

مع الحفاظ على التوافق مع الاستدعاءات القديمة.

## ما لم يتم تغييره عمداً

لم يتم إعادة تصميم:

- منطق إنشاء الفاتورة.
- منطق حركات المخزون.
- منطق التأثير المالي.
- منطق السندات المرتبطة.
- بنية الجداول.

هذه المرحلة Wrapper آمن فقط، وليست إعادة بناء للفواتير.

## ملاحظة مهمة
في Remote mode لا يوجد endpoint مخصص حالياً لـ `has_linked_vouchers`. لذلك `RemoteInvoiceGateway.has_linked_vouchers()` يعيد `False` كفحص واجهة فقط، بينما القاعدة النهائية تبقى enforced server-side داخل update/delete endpoints.

## الفحص

- `python3 -m compileall -q alrajhi_client alrajhi_server`: ناجح.
- فحص الاستيراد المباشر لـ `invoice_dao` داخل `core/views`: لا يوجد.
- الاستخدام المباشر لـ `invoice_dao` محصور داخل `gateways/local/invoice_gateway.py`.

## المرحلة التالية المقترحة
Phase 6 يجب أن تكون `VoucherGateway` لأن السندات مرتبطة مباشرة بالفواتير، لكنها أقل تعقيداً من إعادة بناء Inventory Ledger.
