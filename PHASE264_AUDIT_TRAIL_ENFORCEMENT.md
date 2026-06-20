# PHASE264 — Audit Trail Enforcement

## الهدف
توحيد سجل المراقبة عبر كل أسطح النظام التي تم تثبيتها في المراحل السابقة:

- Document Shell
- List Workspace
- Report Shell
- Operational Shell
- API server routes
- Client/server mode

هذه المرحلة لا تستبدل audit logs الموجودة في الخدمات؛ بل تضيف عقدًا مركزيًا وحماية تشغيلية للأحداث التي كانت ناقصة، خصوصًا الطباعة والتصدير وأوامر الـ workspace والعمليات التشغيلية في POS والمطعم.

## الملفات الرئيسية

### Client contract

- `alrajhi_client/workspace/audit/audit_contract.py`
- `alrajhi_client/workspace/audit/audit_event_policy.py`
- `alrajhi_client/workspace/audit/__init__.py`

### Client gateways

- `alrajhi_client/core/services/audit_service.py`
- `alrajhi_client/gateways/audit_gateway.py`
- `alrajhi_client/gateways/local/audit_gateway.py`
- `alrajhi_client/gateways/remote/audit_gateway.py`
- `alrajhi_client/database/connection_rest.py`

### UI / operational integration

- `alrajhi_client/views/main_window.py`
- `alrajhi_client/workspace/operational/operational_shell_contract.py`

### Server

- `alrajhi_server/api/audit_log.py`
- `alrajhi_server/api/audit_utils.py`
- `alrajhi_server/services/audit_trail_policy.py`
- `alrajhi_server/database/migrations.py`

### Audit tool

- `tools/audit_trail_contract_audit.py`
- `tools/audit_outputs/audit_trail_contract_matrix.csv`

### Tests

- `tests/test_phase264_audit_trail_enforcement.py`

## ما تم

1. إنشاء عقد audit مركزي يجمع أحداث:
   - الوثائق: view/save/delete/print/export/approve/cancel
   - القوائم: open/search/filter/create/delete/print/export
   - التقارير: view/print/export
   - التشغيل: POS/Restaurant operations

2. إضافة metadata منظمة لسجل التدقيق:
   - `audit_scope`
   - `permission_key`
   - `branch_id`
   - `event_category`

3. إضافة migration آمن:
   - `migrate_phase264_audit_contract_columns(conn)`

4. توسيع LocalAuditGateway لتخزين metadata الجديدة.

5. تحويل RemoteAuditGateway من no-op إلى إرسال audit event إلى:
   - `POST /api/audit_log`

6. إضافة endpoint خادمي لقبول client-side audit events، وهذا مهم لأحداث مثل browser print/export التي لا تمر دائمًا عبر route تجاري واضح.

7. ربط `MainWindow` بأحداث audit عند:
   - تنفيذ save/print/export من الشريط العام
   - رفض العملية بسبب الصلاحيات

8. إضافة helper في OperationalShellPermissionBinder لتسجيل:
   - operation allowed
   - operation denied

9. إضافة helper خادمي:
   - `audit_api_event(...)`
   - `audit_print_export(...)`

10. إضافة أداة audit matrix لاكتشاف أي surface بلا audit coverage.

## نتائج الفحص

- `compileall`: ناجح
- `pytest -q`: `217 passed, 1 warning`

## ملاحظة

لا تزال بعض الخدمات تسجل audit business events مباشرة مثل إنشاء/تعديل الفواتير والمواد والسندات. هذا صحيح ومقصود. عقد Phase264 يغطي الطبقة العرضية والتشغيلية والمتقاطعة، ولا يلغي audit الموجود في الخدمات.
