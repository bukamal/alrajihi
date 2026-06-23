# Phase 352 — Brand Identity Visual System

## الهدف

تأسيس طبقة هوية بصرية موحدة مستوحاة من شعار المشروع، بحيث تكون ألوان النظام، شاشات التحميل، تسجيل الدخول، التفعيل، شريط القوائم، شريط الإجراءات، التبويبات، الجداول، الأزرار والنوافذ مبنية على Tokens مركزية بدل ألوان وأحجام متفرقة.

## نطاق التنفيذ

- أضيف عقد هوية بصري PyQt-free في `alrajhi_client/theme/identity.py`.
- تم توسيع `theme/brand.py` بألوان مستخرجة من الشعار: navy/blue/teal/gold/sand مع مفاتيح Light/Dark.
- تم تحديث QSS العالمي ليشمل:
  - التبويبات الرئيسية والفرعية.
  - شريط القوائم.
  - شريط الإجراءات.
  - شاشات التحميل وتسجيل الدخول والتفعيل.
  - الجداول والخلية النشطة.
  - النوافذ والحوارات.
  - أزرار النظام.
- تم تحديث `DesignSystem` ليعرض Helpers موحدة مثل `brand_gradient` و `apply_visual_role`.
- تم ربط شاشة التحميل، تسجيل الدخول، والتفعيل بقياسات وألوان الهوية المركزية.

## الملفات الرئيسية

- `alrajhi_client/theme/identity.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/theme/__init__.py`
- `alrajhi_client/ui/design_system.py`
- `alrajhi_client/views/splash_screen.py`
- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/views/dialogs/activation_dialog.py`
- `alrajhi_client/workspace/quality/brand_identity_visual_contract.py`
- `tools/phase352_brand_identity_visual_guard.py`
- `tests/test_phase352_brand_identity_visual_system.py`

## سياسة الهوية

- لا يتم إدخال ألوان جديدة في الواجهات مباشرة عند إضافة شاشة جديدة.
- يجب استخدام `theme.brand` أو `ThemeManager` أو `DesignSystem`.
- كل شاشة تحميل/تسجيل دخول/تفعيل يجب أن تستخدم الشعار ومقاييس الهوية.
- كل تبويب يجب أن يبدو كعنصر هوية واضح، مع تبويب نشط مميز.
- الجداول يجب أن تستخدم Header موحد وخلية حالية واضحة.
- النوافذ والحوارات يجب أن تستخدم رأس/محتوى/أزرار متناسقة.

## التحقق

- `tools/phase352_brand_identity_visual_guard.py` يولد:
  - `tools/audit_outputs/brand_identity_visual_matrix.csv`
  - `tools/audit_outputs/brand_identity_visual_summary.json`
- تم تسجيل المرحلة في Release Gate.
