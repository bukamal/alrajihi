# PHASE261 — Branch Access Enforcement Audit

## الهدف
توحيد إنفاذ الفروع بعد توحيد RBAC في Phase260. وجود جدول `user_branch_access` لا يكفي وحده؛ يجب أن تعرف كل واجهة/قائمة/تقرير/سطح تشغيل من أين يأخذ `branch_id`، ومتى يجب فلترته في العميل، ومتى يجب إنفاذه في API/الخادم.

## ما تم

### 1. عقد مركزي للفروع
أضيف:

`alrajhi_client/workspace/branches/branch_access_contract.py`

العقد يجمع أسطح المشروع من:

- Document Shell
- List Workspace
- Report Shell
- Operational Shell

ويحدد لكل سطح:

- `branch_policy`
- `enforcement`
- `branch_source`
- `permission_view`
- `api_resource`
- `network_mode`
- `requires_server_filter`
- `requires_payload_branch`
- `requires_allowed_branch_check`

### 2. Runtime BranchAccessPolicy للعميل
أضيف:

`alrajhi_client/workspace/branches/branch_access_policy.py`

ويوفر:

- `can_view_all_branches()`
- `allowed_branch_ids()`
- `can_access_branch(branch_id)`
- `effective_branch_id(requested_branch_id)`
- `require_branch_access(branch_id)`
- `ensure_payload_branch(payload)`
- `scope_query_params(requested_branch_id)`
- `filter_records(records)`

### 3. ربط BranchService
تم توسيع:

`alrajhi_client/core/services/branch_service.py`

حتى لا يختار فرعًا حاليًا خارج صلاحيات المستخدم، ويضيف wrappers مركزية:

- `can_access_branch`
- `require_branch_access`
- `scoped_query_params`

### 4. Server BranchAccessPolicy
أضيف:

`alrajhi_server/services/branch_access_policy.py`

ويوفر للخادم:

- `can_view_all_branches(user_id)`
- `allowed_branch_ids(user_id)`
- `require(user_id, branch_id)`
- `effective_branch_id(user_id, requested_branch_id)`
- `scope_sql(user_id, alias, branch_column, requested_branch_id)`

هذا يسمح لاحقًا بإدخال فلترة الفروع في routes/repositories بدون تكرار منطق `user_branch_access`.

### 5. API branch scope
تم توسيع `/api/rbac/me` ليعيد:

- `can_view_all_branches`
- `branch_scope_mode`

وتم توسيع RestClient بدوال:

- `get_user_branch_access(user_id)`
- `get_my_branch_scope()`

### 6. أداة تدقيق
أضيف:

`tools/branch_access_contract_audit.py`

وتخرج matrix إلى:

`tools/audit_outputs/branch_access_contract_matrix.csv`

## نتائج الفحص

- `compileall`: ناجح
- `tools/branch_access_contract_audit.py`: ناجح
- اختبارات Phase261: ناجحة

## ملاحظة معمارية
هذه المرحلة لا تدّعي أن كل SQL route في الخادم صار يفلتر branch_id فعليًا بعد. هي تضع العقد، runtime helper، وserver helper، وتكشف الأسطح التي تتطلب server filtering. المرحلة التالية يجب أن تبدأ بإدخال `scope_sql()` تدريجيًا في routes الأكثر حساسية: الفواتير، المرتجعات، المستودعات، الصناديق، POS، المطعم، والتقارير.
