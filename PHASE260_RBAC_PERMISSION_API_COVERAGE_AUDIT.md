# PHASE260_RBAC_PERMISSION_API_COVERAGE_AUDIT

## الهدف
توحيد تغطية الصلاحيات بين عقود الواجهات (`Document Shell`, `List Workspace`, `Report Shell`, `Operational Shell`) وبين نظام RBAC الفعلي في العميل والخادم.

## ما تم

- إضافة عقد مركزي للصلاحيات:
  - `alrajhi_client/workspace/security/rbac_contract.py`
- العقد يجمع مفاتيح الصلاحيات المطلوبة من:
  - `DocumentDescriptor`
  - `ListWorkspaceDescriptor`
  - `ReportShellDescriptor`
  - `OperationalShellDescriptor`
- إضافة مصفوفة أدوار افتراضية تغطي:
  - `admin`
  - `manager`
  - `accountant`
  - `cashier`
  - `viewer`
- إضافة migration خادمي idempotent:
  - `migrate_phase260_rbac_contract_permissions(conn)`
- هذا migration يضيف كل الصلاحيات canonical مثل:
  - `sales_invoices.update`
  - `purchase_returns.print`
  - `items.print`
  - `reports.print`
  - `pos.receipt.print`
  - `restaurant.kitchen_ticket.print`
- إضافة remote gateway فعلي:
  - `alrajhi_client/gateways/remote/rbac_gateway.py`
- تعديل factory:
  - `create_rbac_gateway()` يستخدم `RemoteRBACGateway` في وضع العميل/السيرفر بدل `NullRBACGateway` متى كان `RestClient` متاحًا.
- دمج fallback role defaults في العميل مع عقد Phase260.
- إضافة أداة فحص:
  - `tools/rbac_permission_contract_audit.py`
- الأداة تخرج:
  - `tools/audit_outputs/rbac_permission_contract_matrix.csv`

## القاعدة المعمارية
أي صلاحية تصرح بها الواجهة يجب أن تكون:

1. موجودة في RBAC contract.
2. مزروعة في جدول `permissions` على الخادم.
3. مضافة إلى أدوار النظام الافتراضية حيث يلزم.
4. قابلة للوصول عبر `/api/rbac` في وضع الشبكة.
5. غير معتمدة على fallback محلي فقط.

## ملاحظات
- لم تُلغَ الصلاحيات القديمة مثل `invoices.edit` و `returns.edit`؛ بقيت للتوافق.
- الصلاحيات الجديدة canonical أدق، مثل `sales_invoices.update` بدل `invoices.edit` العام.
- branch access يبقى عبر `user_branch_access` مع مفاتيح `branches.view_all` و `branches.manage_all`.
