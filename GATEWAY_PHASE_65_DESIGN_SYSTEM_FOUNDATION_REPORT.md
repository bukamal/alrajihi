# GATEWAY PHASE 65 — DESIGN SYSTEM FOUNDATION

## الهدف
تأسيس طبقة هوية بصرية مركزية لنظام الراجحي بدل تكرار الألوان داخل الشاشات. هذه المرحلة لا تغيّر منطق العمل ولا تعيد بناء لوحة التحكم أو النوافذ؛ هي أساس موحد للمراحل التالية.

## الملفات المضافة
- `alrajhi_client/theme/__init__.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `tools/verify_design_system.py`

## الملفات المعدلة
- `alrajhi_client/theme_manager.py`
- `alrajhi_client/ui/design_system.py`

## ما تم تطبيقه
- تعريف Palette مركزية لهوية الراجحي:
  - Primary: `#0F3D75`
  - Secondary: `#1E5AA8`
  - Accent: `#2D7FF9`
  - Background: `#F5F7FA`
  - Card: `#FFFFFF`
  - Success/Warning/Danger semantic colors
- إنشاء Light/Dark tokens من مصدر واحد.
- جعل `ThemeManager` يقرأ الألوان من `theme/brand.py` بدل امتلاك قاموس ألوان مستقل.
- فصل توليد QSS في `theme/qss.py`.
- إضافة قواعد موحدة لـ:
  - MainWindow/Dialog/Widget
  - Cards/GroupBox
  - Buttons primary/secondary/danger
  - Inputs
  - Tables + headers + selection
  - MenuBar/Menu
  - ToolBar/ToolButton
  - Startup/Login/Activation/Brand cards
  - ProgressBar
- تحديث Defaults في `ui/design_system.py` لتطابق ألوان الراجحي.
- إضافة Guard مستقل للتحقق من ربط Design System.

## نتائج الاختبار
- `python3 -m compileall -q alrajhi_client`: ناجح.
- `python3 tools/verify_design_system.py`: ناجح.
- `python3 tools/verify_branding_assets.py`: ناجح.
- `python3 tools/architecture_guard.py`: ناجح.

## ملاحظات تنفيذية
- هذه المرحلة تؤسس المرجع البصري فقط.
- ما زالت بعض الشاشات تحتوي Styles محلية قديمة؛ سيتم تنظيفها تدريجيًا في مراحل لاحقة حتى لا نكسر الواجهة دفعة واحدة.
- المرحلة التالية المنطقية: إعادة تصميم لوحة التحكم بناءً على هذه tokens، ثم شريط التنقل، ثم الجداول والنماذج.
