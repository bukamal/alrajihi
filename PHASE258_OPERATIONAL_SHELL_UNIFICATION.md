# PHASE258 — Operational Shell Unification

## الهدف
توحيد واجهات التشغيل عالية الحساسية، خصوصًا POS والمطعم، بعقد مستقل عن Document Shell التحريري.
هذه الواجهات لا تتصرف مثل مستندات تحرير عادية؛ هي جلسات تشغيل مرتبطة بورديات، صناديق، مستودعات، دفع، مطبخ، طباعة، صلاحيات، وإعدادات.

## الملفات الجديدة
- `alrajhi_client/workspace/operational/operational_shell_contract.py`
- `alrajhi_client/workspace/operational/__init__.py`
- `tools/operational_shell_contract_audit.py`
- `tests/test_phase258_operational_shell_unification.py`

## ما تم توحيده
- POS كـ `OperationalShellDescriptor(shell_key="pos")`.
- Restaurant كـ `OperationalShellDescriptor(shell_key="restaurant")`.
- العمليات الحساسة صارت مصرحًا بها في عقد واحد: checkout, suspend, resume, open/close shift, print receipt, send kitchen, record payment, checkout restaurant session.
- كل عملية تصرح عن RBAC permission، إعداد التفعيل، مفتاح اللغة، التصنيف، ومتطلبات الجلسة/الوردية/الصندوق/المستودع.

## الربط العملي
- `POSWidget` أصبح يستدعي `bind_operational_shell(self, 'pos')`.
- `RestaurantPOSWidget` أصبح يستدعي `bind_operational_shell(self, 'restaurant')`.
- `RestaurantDashboard` أصبح يحمل نفس عقد المطعم.

## ما لم يتم تغييره عمدًا
لم يتم تحويل POS أو المطعم إلى `BaseDocumentTab`؛ هذا خطأ معماري. تم إبقاؤهما كسطوح تشغيلية مع عقد منفصل مرتبط بـ DocumentDescriptor.

## نتيجة المرحلة
العقود أصبحت قابلة للفحص في CI بدون PyQt، ويمكن لاحقًا بناء dashboard إدارية تعرض جاهزية POS/Restaurant من حيث الشبكة، العملة، الصلاحيات، الإعدادات والطباعة.
