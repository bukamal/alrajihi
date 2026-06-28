# Phase 419 — Preferences Registry Consolidation

## الهدف

هذه المرحلة لا تضيف إعدادات جديدة للمستخدم، بل تضبط ملكية الإعدادات الموجودة وتمنع استمرار انتشار `QSettings` الخام داخل الشاشات. المشكلة المعمارية بعد Phase 418 أن المشروع صار يملك أكثر من قناة لحفظ نفس النوع من البيانات: إعدادات مستخدم، إعدادات جدول، إعدادات POS، إعدادات شركة، لغة، ثيم، splitters، وأحجام أعمدة.

Phase 419 تضيف سجلًا مركزيًا يعلن لكل Preference:

- المفتاح المنطقي.
- النطاق Scope.
- القيمة الافتراضية.
- نوع القيمة.
- الوصف التشغيلي.

## الملفات المضافة

- `alrajhi_client/core/services/preferences_registry.py`
- `alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py`
- `tools/phase419_preferences_registry_consolidation_guard.py`
- `tests/test_phase419_preferences_registry_consolidation.py`

## الملفات المعدلة

- `alrajhi_client/core/services/user_preferences_service.py`
- `alrajhi_client/features/transactions/grids/transaction_grid_preferences.py`
- `alrajhi_client/features/pos/pos_preferences.py`
- `alrajhi_client/theme_manager.py`
- `alrajhi_client/workspace/quality/release_gate_contract.py`

## النطاقات المركزية

تم تعريف `PreferenceScope` كالتالي:

- `SYSTEM`
- `COMPANY`
- `BRANCH`
- `USER`
- `USER_BRANCH`
- `WORKSTATION`
- `TABLE_LAYOUT`
- `DOCUMENT_TYPE`
- `POS_TERMINAL`

هذا يمنع الخلط بين إعدادات الشركة وإعدادات المستخدم والجهاز والفرع. مثلًا:

- إخفاء رصيد الصندوق: `USER`.
- حالة جدول فاتورة: `DOCUMENT_TYPE`.
- إعدادات POS: `POS_TERMINAL`.
- شعار محلي من مسار جهاز: `WORKSTATION`.
- بيانات الشركة: `COMPANY`.

## ما تم توحيده فعليًا

### 1. UserPreferencesService

أصبح يستخدم:

`PreferencesRegistry + QSettingsPreferenceBackend`

مع الحفاظ على مفاتيح Phase 413 حتى لا تضيع تفضيلات المستخدم المحفوظة سابقًا.

### 2. TransactionGridPreferences

لم يعد يبني مفاتيح layout محليًا فقط. أصبح يستدعي:

`preference_registry.transaction_grid_key(...)`

مع الحفاظ على الشكل القديم للمفتاح:

`transactions/users/{user}/branches/{branch}/profiles/{profile}/{document_type}/{name}`

### 3. POSPreferences

أصبح يستدعي:

`preference_registry.pos_key(...)`

مع الحفاظ على الشكل القديم للمفتاح:

`pos/users/{user}/branches/{branch}/profiles/{profile}/{identity}/{name}`

### 4. ThemeManager

تمت إزالة `QSettings` المباشر منه. حفظ وقراءة الثيم أصبحت عبر:

`user_preferences_service`

## ما لم يتم حذفه عمدًا

لا تزال توجد استخدامات مباشرة لـ `QSettings` في ملفات أخرى. لم يتم حذفها دفعة واحدة حتى لا نكسر مسارات حساسة مثل:

- تسجيل الدخول والجلسة.
- التحكم بالسيرفر المحلي.
- الاتصال بقاعدة البيانات.
- إعدادات الطباعة القديمة.
- واجهات قديمة/معزولة مثل `invoice_dialog.py`.
- إعدادات الشركة والشاشة العامة التي ستحتاج ترحيلًا مستقلًا.

لكن Phase 419 تضيف audit matrix يرصد كل هذه الاستخدامات ويصنفها بدل تركها مجهولة.

## مخرجات التشخيص

عند تشغيل:

```bash
python tools/phase419_preferences_registry_consolidation_guard.py
```

يتم إنتاج:

- `tools/audit_outputs/preferences_registry_consolidation_matrix.csv`
- `tools/audit_outputs/preferences_registry_qsettings_usage.csv`

الأول يثبت سلامة المرحلة. الثاني يعطي قائمة واضحة بكل بقايا `QSettings` الخام وتصنيفها للترحيل اللاحق.

## حدود المرحلة

هذه المرحلة ليست إزالة كاملة لـ `QSettings`. هي مرحلة تأسيس Registry وتوصيل المسارات الأكثر خطورة:

- User preferences.
- Dashboard privacy.
- Theme.
- Transaction grid layout.
- POS layout.

الإزالة الكاملة لباقي `QSettings` يجب أن تكون في مراحل لاحقة صغيرة حتى لا تُخلط إعدادات تشغيل حساسة بإعدادات واجهة.

## القاعدة بعد Phase 419

أي Preference جديد يجب ألا يكتب `QSettings` مباشرة داخل Widget أو Dialog.

المسار الصحيح:

1. تعريف المفتاح والنطاق في `PREFERENCE_DEFINITIONS`.
2. استخدام `PreferencesRegistry` أو Adapter مركزي.
3. إضافة Guard يثبت أن المفتاح مصنف.

