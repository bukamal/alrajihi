# Phase 405 — Basit Reports & Settings Surface

## الهدف
متابعة تطبيق هوية البسيط بعد لوحة التحكم والفواتير والقوائم، وهذه المرحلة تغطي التقارير والإعدادات.

## التقارير
- شريط الفلاتر أصبح سطحًا تشغيليًا واضحًا على نمط البسيط.
- أزرار التحديث والطباعة وإعادة الفلاتر تستخدم نمط `basitToolbarButton`.
- تبويبات التقارير تستخدم أزرق/أصفر البسيط.
- جداول التقارير تستخدم `basitTable` و `basitReportTable`.
- شريط ملخص التقرير يستخدم سطحًا أحمر واضحًا للإجماليات المهمة.

## الإعدادات
- صفحة الإعدادات تستخدم `basitSettingsSurface`.
- التبويبات الرئيسية والفرعية تستخدم نفس لغة الأزرق/الأصفر.
- بطاقات الإعدادات أصبحت `basitSettingsCard`.
- أزرار الحفظ والتطبيق في الإعدادات أصبحت موحدة مع أزرار البسيط.

## الحماية
- `tools/phase405_basit_reports_settings_surface_guard.py`
- `tests/test_phase405_basit_reports_settings_surface.py`
- `alrajhi_client/workspace/quality/basit_reports_settings_surface_contract.py`
