# PHASE 356 — Branded Dialogs & System Windows

## الهدف
توحيد مظهر النوافذ المنبثقة والنظامية مع الهوية البصرية الجديدة للمشروع، بحيث لا تبقى نوافذ التأكيد، الإعدادات، الاختيار، طباعة الباركود، وتخصيص الأعمدة منفصلة بصريًا عن بقية النظام.

## النطاق
- النوافذ ذات الإطار الداخلي `FramelessDialog`.
- الحوارات الحديثة التي تمر عبر `apply_modern_dialog`.
- نوافذ الرسائل والتأكيد `QMessageBox` للمسارات الجديدة.
- نافذة تخصيص أعمدة الجداول.
- إشعارات Toast.
- أزرار الحفظ، الإغلاق، الحذف، الأوامر الثانوية داخل النوافذ.

## التغييرات
- إضافة عقد هوية PyQt-free:
  - `alrajhi_client/theme/dialog_identity.py`
- إضافة طبقة Runtime آمنة:
  - `alrajhi_client/ui/dialog_branding.py`
- إضافة خصائص ديناميكية موحدة:
  - `brandDialog`
  - `dialogKind`
  - `dialogSurface`
  - `dialogActionRole`
  - `toastType`
- تحديث QSS العالمي بمسارات Phase 356.
- تحديث `FramelessDialog` ليستخدم:
  - `BrandDialogFrame`
  - `BrandDialogHeader`
  - `BrandDialogTitle`
- تحديث `apply_modern_dialog` ليعيد تمرير النوافذ إلى `apply_branded_dialog`.
- تحديث Toast ليستمد ألوانه من ThemeManager والـ brand tokens.

## السياسة البصرية
- زر الحفظ/الموافقة/التفعيل/الدخول = Primary.
- زر الإغلاق/الإلغاء = Close/Neutral.
- زر الحذف/التجاهل = Danger.
- رأس النافذة يحمل لون الهوية وخط accent ذهبي.
- محتوى النافذة وبطاقة العنوان يستخدمان الخلفيات والحدود المركزية.

## التحقق
- `tools/phase356_branded_dialogs_system_windows_guard.py`
- `tests/test_phase356_branded_dialogs_system_windows.py`
- تسجيل Phase 356 داخل Release Gate.
