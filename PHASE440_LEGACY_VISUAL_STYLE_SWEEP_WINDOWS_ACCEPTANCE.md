# Phase 440 — Legacy Visual Style Sweep & Windows Runtime Acceptance Matrix

## الهدف
بعد Phase 439 أصبح تطبيق الهوية البصرية مركزيًا عند فتح الصفحات والتبويبات، لكن بقي خطر أن بعض الشاشات القديمة تملك `setStyleSheet()` محليًا أو ألوانًا حرفية قد تطغى على الهوية. هذه المرحلة لا تغيّر منطق الأعمال، بل تضيف طبقة تدقيق وحراسة لتصنيف الديون البصرية وتجهيز مصفوفة قبول Windows.

## ما تم
- رفع `project_visual_identity_phase` إلى 440.
- إضافة `legacy_visual_style_sweep_phase` و `windows_runtime_acceptance_phase` إلى tokens.
- توسيع `runtime_visual_polish.py` ليضع خصائص:
  - `visualIdentitySweepPhase`
  - `visualStyleSource`
  - `workspace_scroll`
  - `workspace_stack`
  - `workspace_splitter`
- توسيع QSS المركزي ليغطي Phase 440 والتبويبات والـ scroll/splitter containers.
- إضافة تدقيق static لكل `setStyleSheet()` داخل views/features/ui وتصنيفه بدل تركه مجهولًا.
- إضافة مصفوفة قبول Windows بدقات/Scaling/LTR/RTL وسطح اختبار واضح.

## المخرجات
- `tools/audit_outputs/legacy_visual_style_sweep.csv`
- `tools/audit_outputs/legacy_visual_style_sweep_summary.json`
- `tools/audit_outputs/windows_runtime_acceptance_matrix_phase440.csv`
- `tools/audit_outputs/windows_runtime_acceptance_matrix_phase440_summary.json`

## حدود المرحلة
هذه المرحلة لا تدعي إزالة كل QSS قديم. هي تجعل الديون البصرية مرئية ومصنفة، وتضمن أن أي واجهة تُفتح عبر المسار الحديث تحصل على الهوية المركزية. إزالة الـ QSS المحلي من كل شاشة ستكون Sweep لاحقًا إذا ظهر تعارض بصري محدد.

## اختبار Windows المقترح
يجب تشغيل EXE على الأقل على:
- 1366×768 / 100% / Arabic RTL
- 1366×768 / 125% / Arabic RTL
- 1920×1080 / 100% / Arabic RTL
- 1920×1080 / 125% / Arabic RTL
- 1366×768 / 100% / English LTR
- 1920×1080 / 125% / German LTR

الأسطح المطلوب اختبارها: Splash، Login، Overlay، Dashboard، الشريط العلوي، POS، المطعم، ملء الشاشة، الجداول التحريرية، الطباعة.
