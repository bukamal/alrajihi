# Phase 295 — Restaurant Operation Governance Enforcement

## الهدف

توسيع حوكمة المطعم بحيث لا تبقى الصلاحيات مقتصرة على فتح الجلسة، إضافة السطر، الإرسال للمطبخ، الدفع، والإغلاق فقط. هذه المرحلة تجعل العمليات التشغيلية الحساسة التي أضيفت في المراحل الأخيرة تمر عبر نفس طبقة الصلاحيات والإعدادات والتدقيق.

## النطاق

- حجز الطاولات وإلغاء الحجز.
- نقل الجلسة بين الطاولات.
- دمج الطاولات.
- نقل سطر طلب إلى طاولة أخرى.
- تقسيم الفاتورة.
- سير عمل النادل.
- إدارة محطات المطبخ.
- إدارة الإضافات والوصفات.
- تشغيل السفري والتوصيل.
- إدارة طابعات المطعم وطابور الطباعة.
- عرض تحليلات المطعم.

## التغييرات

- توسعة `RestaurantOperationPolicy` بعمليات مطعم تشغيلية جديدة.
- ربط العمليات الجديدة بمفاتيح إعدادات `restaurant/operations/allow_*`.
- ربط العمليات الجديدة بأفعال RBAC داخل `PermissionService`.
- إضافة قيود legacy security اختيارية لكل عملية حساسة.
- تحديث `RestaurantService` حتى يطبق `require()` و `audit log` قبل تنفيذ العمليات الحساسة.
- تحديث شريط عمليات الطاولات داخل `RestaurantDashboard` حتى يحترم الإعدادات والصلاحيات عند الإظهار والتفعيل.
- إضافة ترجمات عربية/إنكليزية/ألمانية لتسميات العمليات الجديدة.
- تحديث Release Readiness Gate لتثبيت المرحلة.

## ملاحظات تشغيلية

كل العمليات الافتراضية تبقى مفعلة لضمان عدم كسر السلوك الحالي. يمكن تقييدها لاحقًا من RBAC أو من مفاتيح الإعدادات/الأمان.

## التحقق

- `python tools/architecture_guard.py`
- `python -m compileall -q alrajhi_client alrajhi_server tests tools`
- `pytest -q tests/test_phase295_restaurant_operation_governance_enforcement.py`
- Restaurant phase regression tests.
- Release readiness and packaging guards.
