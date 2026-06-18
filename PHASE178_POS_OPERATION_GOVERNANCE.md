# Phase 178 — POS Operation Governance

## الهدف

بعد فصل واجهة الدفع في POS إلى `POSPaymentShell`، أصبحت العمليات الحساسة بحاجة إلى طبقة حوكمة موحدة بدل أن تكون أزرارًا أو اختصارات مباشرة داخل `POSWidget`.

هذه المرحلة تضبط عمليات:

- إنهاء البيع.
- تعليق البيع.
- استرجاع بيع معلق.
- حذف سطر.
- تفريغ السلة.
- فتح وردية.
- إغلاق وردية.
- طباعة الإيصال.

## الملفات الرئيسية

- `alrajhi_client/core/services/pos_operation_policy.py`
- `alrajhi_client/views/widgets/pos_widget.py`
- `alrajhi_client/core/services/pos_service.py`
- `alrajhi_client/core/services/permission_service.py`
- `alrajhi_client/core/services/rbac_service.py`
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/database/migrations.py`
- `alrajhi_server/database/migrations.py`
- `alrajhi_client/i18n/translator.py`
- `tools/phase178_pos_operation_governance_guard.py`

## ما تم

### 1. POSOperationPolicy

أضيفت طبقة مركزية داخل `core/services` حتى لا يعيش قرار الصلاحية داخل الواجهة فقط:

```text
core/services/pos_operation_policy.py
```

وتدعم العمليات التالية:

```text
checkout
suspend
resume
remove_line
clear_cart
open_shift
close_shift
print_receipt
```

كل عملية تمر عبر:

- settings toggle.
- permission service.
- RBAC permission.
- audit helper.

### 2. ربط POSWidget

تم ربط أزرار POS واختصاراته بآلية:

```python
_require_pos_operation(operation)
```

بدل تنفيذ العملية مباشرة.

### 3. ربط POSService

أصبحت العمليات الحساسة داخل `POSService` تتحقق أيضًا من policy:

- `remove_line()`
- `remove_line_at()`
- `clear()`
- `suspend()`
- `resume()`
- `checkout()`

هذا يمنع تجاوز الواجهة واستدعاء service مباشرة لتنفيذ عملية غير مسموحة.

### 4. صلاحيات RBAC جديدة

أضيفت صلاحيات:

```text
pos.suspend
pos.resume
pos.line.remove
pos.cart.clear
pos.shift.open
pos.shift.close
pos.receipt.print
```

مع الإبقاء على:

```text
pos.use
```

### 5. إعدادات POS operations

أضيفت إلى `settings_service.get_pos_settings()` بنية:

```python
operations = {
    allow_checkout,
    allow_suspend,
    allow_resume,
    allow_remove_line,
    allow_clear_cart,
    allow_open_shift,
    allow_close_shift,
    allow_print_receipt,
    confirm_clear_cart,
    confirm_partial_payment,
}
```

### 6. قاعدة البيانات والخادم

تمت إضافة الصلاحيات الجديدة إلى migrations في العميل والخادم حتى تظهر في نظام الأدوار والصلاحيات.

### 7. الترجمة

أضيفت مفاتيح عربية/ألمانية/إنجليزية لرسائل رفض العمليات وأسمائها.

## الفحوص

تم تشغيل:

```text
python -m compileall -q alrajhi_client alrajhi_server tools/phase178_pos_operation_governance_guard.py
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
python tools/phase171_material_document_guard.py
python tools/phase172_unit_barcode_api_guard.py
python tools/phase173_material_workspace_guard.py
python tools/phase174_material_security_guard.py
python tools/phase175_pos_touch_guard.py
python tools/phase176_pos_visual_grid_guard.py
python tools/phase177_pos_payment_shell_guard.py
python tools/phase178_pos_operation_governance_guard.py
```

## النتيجة

POS صار أقرب إلى نظام مؤسسي: الواجهة، الخدمة، الصلاحيات، الإعدادات، الترجمة، والـ RBAC كلها تتعامل مع العمليات الحساسة كمجموعة موحدة، وليس كأزرار متفرقة.
