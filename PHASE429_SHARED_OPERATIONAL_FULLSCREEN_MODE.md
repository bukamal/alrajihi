# Phase 429 — Shared Operational Fullscreen Mode

## الهدف

توحيد وضع ملء الشاشة التشغيلي لكل واجهات التشغيل بدل بقاء كل شاشة مسؤولة عن `showFullScreen()` بشكل محلي. الوضع الجديد يخفي شريط عنوان النظام عبر `showFullScreen()`، ويخفي كروم المشروع الداخلي من مكان واحد: شريط القوائم، شريط الإجراءات، مركز التنبيهات، شريط التبويبات، وأي `QToolBar` حقيقي.

## ما تم تنفيذه

- إضافة `OperationalFullscreenController` في `alrajhi_client/ui/operational_fullscreen_controller.py`.
- إضافة زر مشترك في `UnifiedActionBar` باسم `fullscreen`.
- ربط الزر داخل `MainWindow` عبر `toggle_operational_fullscreen()`.
- دعم `F11` كاختصار عام على مستوى التطبيق.
- جعل `Esc` يخرج من ملء الشاشة أولًا قبل الرجوع للوحة التحكم.
- إضافة زر عائم `OperationalFullscreenExitButton` للخروج من الوضع بعد إخفاء الشريط.
- تحويل زر POS المحلي إلى delegate للـ MainWindow بدل امتلاك `showFullScreen()`.
- إضافة زر مماثل في واجهة المطعم البسيطة وواجهة طلبات المطعم/الكافي، وكلاهما يستدعي نفس الـ controller.

## القاعدة المعمارية

لا يجوز لأي واجهة تشغيلية أن تستدعي `showFullScreen()` مباشرة. المالك الوحيد هو:

`OperationalFullscreenController`

واجهات POS / Restaurant / Cafe يمكنها فقط استدعاء:

`window.toggle_operational_fullscreen()`

## السلوك

- `F11`: دخول/خروج من وضع ملء الشاشة التشغيلي.
- `Esc`: إذا كان الوضع فعالًا يخرج منه فقط؛ إذا لم يكن فعالًا يرجع للوحة التحكم كما في السلوك السابق.
- زر عائم يظهر في وضع ملء الشاشة للخروج.
- عند الخروج، يتم استعادة حالة العناصر كما كانت قبل الدخول، وليس إظهارها قسرًا.

## التحقق

- `tools/phase429_operational_fullscreen_guard.py`
- `tests/test_phase429_operational_fullscreen.py`
- `tools/audit_outputs/operational_fullscreen_matrix.csv`
