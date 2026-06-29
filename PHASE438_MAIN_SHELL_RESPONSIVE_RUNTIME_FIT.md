# Phase 438 — Main Shell Responsive Runtime Fit

## الهدف

بعد تسريع فتح الواجهة في Phase 436 وتحديث هوية لوحة التحكم في Phase 437، بقيت مشكلة Runtime ظاهرة في بيئات X11/VNC/Termux/HiDPI: الواجهة الرئيسية قد تظهر كنافذة ثابتة داخل مساحة أكبر، تاركة نطاقات سوداء أو غير مستخدمة حولها، أو قد تفرض حدًا أدنى أكبر من الشاشة على الأجهزة الصغيرة.

Phase 438 يجعل نافذة المشروع الرئيسية **screen-aware** بدل الاعتماد على أرقام ثابتة مثل `1200x700` و `1400x900`.

## ما تغيّر

- إضافة وحدة مركزية:

  `alrajhi_client/ui/main_shell_runtime_fit.py`

- تطبيق سياسة شاشة واعية على `MainWindow`:
  - لا تفرض حدًا أدنى أكبر من الشاشة المتاحة.
  - تضبط الحجم الابتدائي حسب `availableGeometry`.
  - تبدأ Maximized افتراضيًا حتى تستغل لوحة التحكم كامل سطح العمل.
  - يمكن تعطيل ذلك مؤقتًا عبر:

    `ALRAJHI_WINDOWED_START=1`

- تعديل مسار إظهار الواجهة بعد تسجيل الدخول في:

  `alrajhi_client/main.py`

  ليستخدم:

  `show_main_window_runtime_fitted(window)`

  بدل `window.show()` المباشر.

- إضافة معلومات سياسة الملاءمة إلى `startup_timeline` عبر context.

- تحسين لوحة التحكم لتجنب horizontal scroll/clip في بيئات العرض الضيقة:
  - إيقاف horizontal scrollbar داخل Dashboard scroll area.
  - تقليل الهوامش والتباعد قليلًا.
  - إضافة property `dashboardResponsivePhase=438`.

## حدود المرحلة

هذه المرحلة لا تغيّر منطق لوحة التحكم، ولا الصندوق، ولا التبويبات، ولا الصلاحيات، ولا الأداء الداخلي. هي فقط تضبط **كيف تظهر الواجهة على الشاشة**.

## التحقق

- compileall ناجح.
- Guard Phase 438 يثبت وجود سياسة Runtime Fit.
- اختبارات Phase 438 تؤكد أن MainWindow لم يعد يعتمد على `window.show()` المباشر ولا على fixed geometry ثابت فقط.
