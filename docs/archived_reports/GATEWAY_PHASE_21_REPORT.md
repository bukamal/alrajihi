# Gateway Phase 21 Report

## الهدف
تثبيت حدود الطبقات بعد Phase 20 وإزالة آخر استيراد مباشر لحزمة `database` من نقطة تشغيل العميل `main.py`.

## التغييرات

### 1. نقل تهيئة قاعدة البيانات خلف SystemService/SystemGateway
تمت إضافة العمليات التالية إلى عقد `SystemGateway`:

- `ensure_local_database()`
- `ensure_server_database()`
- `configure_server_database_path()`

وبذلك أصبح `main.py` يستدعي:

```text
system_service.ensure_local_database()
system_service.ensure_server_database()
system_service.configure_server_database_path()
```

بدلاً من الاستيراد المباشر:

```text
from database import ensure_db
from alrajhi_server.database.migrations import ensure_db
```

### 2. تعديل الملفات

```text
alrajhi_client/gateways/system_gateway.py
alrajhi_client/gateways/local/system_gateway.py
alrajhi_client/core/services/system_service.py
alrajhi_client/main.py
tools/architecture_guard.py
```

### 3. تقوية architecture_guard
أصبح الحارس يمنع داخل الطبقات المحمية:

```text
views
core/services
currency.py
main.py
```

أي استيراد مباشر من:

```text
database
alrajhi_client.database
database.dao
database.repositories
DatabaseConnection
core.server_control
SQL execute/executemany/executescript
```

## النتيجة

```text
architecture_guard: passed
compileall: passed
zip test: passed
legacy DatabaseConnection exceptions: 0
```

## الأثر المعماري
بعد هذه المرحلة أصبح مسار تهيئة قاعدة البيانات أيضاً خلف Service/Gateway، وليس فقط عمليات القراءة والكتابة اليومية. هذا يغلق ثغرة معمارية كانت تسمح لنقطة التشغيل بالوصول المباشر إلى طبقة التخزين.

## المرحلة التالية المقترحة
Phase 22: بدء Inventory Ledger بشكل تحضيري غير مدمّر:

- إضافة migration للجداول فقط.
- إضافة DAO/Gateway للـ Ledger.
- عدم تغيير حساب الرصيد الحالي بعد.
- إضافة reconciliation/report يقارن الرصيد الحالي مع ledger لاحقاً.
