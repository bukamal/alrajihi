# Phase 263 — POS / Restaurant Branch Scope Enforcement

## الهدف

هذه المرحلة تنقل رقابة الفروع من العقود العامة إلى مسارات التشغيل الخاصة بالمطعم وواجهات التشغيل، مع الحفاظ على نموذج الشبكة/API وتعدد المستخدمين.

## ما تم

- إضافة helper مركزي:
  - `alrajhi_server/services/restaurant_branch_scope.py`
- إضافة scope canonical جديد:
  - `restaurant_scope(...)` داخل `branch_scoped_sql.py`
- إضافة أعمدة فرع تشغيلية آمنة ومتوافقة مع قواعد قديمة:
  - `restaurant_tables.branch_id`
  - `restaurant_sessions.branch_id`
  - `kitchen_tickets.branch_id`
  - `restaurant_payments.branch_id`
  - `restaurant_reservations.branch_id`
- ربط مسارات المطعم بـ `restaurant_branch_guard()` حتى يتم فحص الوصول للفرع قبل عمليات:
  - فتح الطاولة
  - قراءة الجلسة
  - إضافة البنود
  - الإرسال للمطبخ
  - تحديث حالة البند
  - الدفع
  - checkout
  - تذاكر المطبخ
  - الحجوزات
  - نقل/دمج/تقسيم الجلسات
  - takeaway/delivery
  - split bills
  - print jobs
- فلترة قوائم التشغيل الحساسة حسب الفروع المسموحة:
  - tables
  - kitchen tickets
  - restaurant orders
- ربط فواتير المطعم الناتجة عن checkout بـ `branch_id` حتى تدخل في نفس رقابة الفواتير والتقارير.

## ملاحظات تصميمية

- السجلات القديمة التي لا تحتوي `branch_id` تبقى مقروءة للتوافق، ولا يتم إخفاؤها قسرًا عن قواعد البيانات القديمة.
- عند إنشاء كيان جديد، يتم استخدام `branch_access_policy.effective_branch_id(...)` لتحديد الفرع الفعلي للمستخدم.
- لم يتم تحويل POS/Restaurant إلى Document Shell؛ بقيت Operational Shell، لكن أصبحت branch-aware على مستوى API.

## تحقق

- `compileall` ناجح.
- الاختبار المستهدف `test_phase263_pos_restaurant_branch_scope_enforcement.py` يتحقق من وجود الحارس، helper، أعمدة branch، وربط checkout بفرع الجلسة.
