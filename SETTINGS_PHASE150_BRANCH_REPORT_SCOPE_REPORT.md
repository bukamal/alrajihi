# SETTINGS PHASE 150 — Branch Report Scope & Branch Permissions

## الهدف
تحويل دعم الفروع من مجرد فرع افتراضي وتشخيص إلى نطاق تشغيلي فعلي للتقارير، مع احترام صلاحيات المستخدم.

## ما تم تنفيذه

### 1. صلاحيات الفروع
تم توسيع `PermissionService` بإجراءات جديدة:

- `ACTION_VIEW_ALL_BRANCHES`
- `ACTION_MANAGE_ALL_BRANCHES`

وإعدادات سياسة جديدة:

- `security/restrict_branch_scope_for_non_admin`
- `security/allow_non_admin_view_all_branches`
- `security/allow_non_admin_manage_all_branches`

النتيجة: المستخدم العادي يمكن تقييده بفرعه الحالي، بينما المدير يرى كل الفروع.

### 2. نطاق تقارير الفروع
تمت إضافة دوال في `BranchService`:

- `report_scope(requested_branch_id=None)`
- `warehouses_for_scope(branch_id=None)`

النتيجة: التقارير تستطيع معرفة هل تعمل على كل الفروع أو على فرع محدد.

### 3. ربط التقارير بنطاق الفرع
تم توسيع `ReportingService` بدوال ومحددات فرع:

- `branch_report_scope()`
- `warehouse_balances(..., branch_id=None)`
- `warehouse_movements(..., branch_id=None)`
- `warehouse_valuation(..., branch_id=None)`
- `item_movement_report(..., branch_id=None)`
- `invoice_profit_report(..., branch_id=None)`
- `net_profit_report(..., branch_id=None)`
- `smart_items_report(..., branch_id=None)`

إذا كان المستخدم لا يملك صلاحية عرض كل الفروع، يتم تجاهل الفرع المطلوب وتطبيق فرعه الفعلي.

### 4. تشخيص نطاق الفروع
تمت إضافة فحص إلى `SystemService.integrity_checks()`:

- `branch_report_scope`

يعرض نطاق التقارير الحالي، مثل:

- `all:كل الفروع`
- `branch:فرع دمشق`

## الأثر العملي
قبل هذه المرحلة، الفروع كانت موجودة في الجداول وبعض المستندات، لكن التقارير لم تكن محكومة مركزيًا بنطاق الفرع.

بعد هذه المرحلة، أصبحت التقارير الرئيسية قابلة للتصفية حسب الفرع، وتستطيع الالتزام بصلاحيات المستخدم.

## ملاحظات
لم يتم إنشاء نظام فروع من الصفر لأن الفروع موجودة أصلًا. هذه المرحلة ركزت على الحوكمة وربط الفروع بالتقارير والصلاحيات.
