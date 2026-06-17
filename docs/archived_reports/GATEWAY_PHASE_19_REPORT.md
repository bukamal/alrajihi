# Gateway Phase 19 Report

## الهدف
تنظيف نقطة تشغيل التطبيق الرئيسية من الوصول المباشر إلى `DatabaseConnection` و `UserRepository`، وإدخالها ضمن الحدود المعمارية المحمية.

## التغييرات المنفذة

### 1. توسيع SystemGateway
أضيفت إلى عقد `SystemGateway` الدوال التالية:

- `mode()`
- `set_mode(mode)`
- `server_url()`
- `data_source_label()`

وبذلك أصبحت معلومات وضع التشغيل ومصدر البيانات تمر عبر:

```text
main.py → system_service → SystemGateway → LocalSystemGateway → DatabaseConnection
```

بدلاً من:

```text
main.py → DatabaseConnection
```

### 2. تنظيف start_periodic_backup
تمت إزالة الاستيراد المباشر:

```python
from database.connection import DatabaseConnection
```

واستبداله بـ:

```python
system_service.is_remote()
```

### 3. تنظيف main startup flow
تم استبدال:

```python
DatabaseConnection().mode
DatabaseConnection().server_url
DatabaseConnection().is_remote()
DatabaseConnection().data_source_label()
```

بـ:

```python
system_service.mode()
system_service.server_url()
system_service.is_remote()
system_service.data_source_label()
```

### 4. إزالة UserRepository من main.py
تم حذف الاستيراد المباشر:

```python
from database import UserRepository
```

لأن `ChangePasswordDialog` يستخدم فعلاً `user_service.change_password()`، وهذا يكفي لمسار تغيير كلمة المرور. بعد نجاح الحوار يتم تحديث `UserSession` فقط.

### 5. تقوية architecture_guard
تمت إضافة:

```text
alrajhi_client/main.py
```

إلى الملفات المحمية في `tools/architecture_guard.py`.

## نتيجة الفحص

```text
architecture_guard: passed
compileall: passed
zip test: passed
```

## الحالة بعد Phase 19

أصبحت نقاط التشغيل التالية خلف Service/Gateway:

- وضع التشغيل المحلي/العميل/الخادم
- server_url
- فحص remote mode
- تسمية مصدر البيانات
- فحص النسخ الاحتياطي الدوري
- تغيير كلمة المرور الإجباري بعد تسجيل الدخول

## ملاحظة
بقي الاستيراد التالي في `main.py` مقبولاً:

```python
from database import ensure_db
```

لأنه bootstrap/migration entrypoint، وليس DAO/Repository ولا مسار تعامل تشغيلي مع البيانات. يمكن لاحقاً نقله إلى `SystemGateway.bootstrap_local_database()` إذا رغبت بتشديد الحدود أكثر.
