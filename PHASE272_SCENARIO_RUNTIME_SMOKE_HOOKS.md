# Phase 272 — Scenario Runtime Smoke Hooks

## الهدف

Phase 271 أنشأ مصفوفة حراسة ثابتة للسيناريوهات. هذه المرحلة تضيف طبقة تشغيلية خفيفة لا تنفذ عمليات مالية حقيقية، لكنها تجعل كل سيناريو قابلًا للفحص من CI أو لاحقًا من شاشة تشخيص داخل التطبيق.

## الملفات المضافة

- `alrajhi_client/workspace/scenarios/scenario_runtime_smoke.py`
- `tools/scenario_runtime_smoke_audit.py`
- `tests/test_phase272_scenario_runtime_smoke_hooks.py`

## ما يغطيه Smoke Plan

لكل خطوة في كل سيناريو:

- وجود العقد الأصلي.
- شكل payload تجريبي آمن.
- route intent بدون إرسال فعلي.
- permission hook.
- settings hook.
- language hook.
- currency hook.
- branch hook.
- print/export hook عند الحاجة.
- audit hook.
- offline hook عند الحاجة.

## السلامة

كل الخطط:

- `safe_for_ci=True`
- `destructive=False`
- لا تستورد PyQt.
- لا تبدأ الخادم.
- لا تكتب فواتير أو سندات أو حركات مخزون.
- callback-mode hooks تُسجل كـ `skipped` إذا لم يقدّم runner خارجي callback صريحًا.

## المخرجات

الأداة تكتب:

- `tools/audit_outputs/scenario_runtime_smoke_matrix.csv`
- `tools/audit_outputs/scenario_runtime_smoke_summary_matrix.csv`
- `tools/audit_outputs/scenario_runtime_smoke_dry_run_results.csv`

## العلاقة بالمراحل السابقة

- تعتمد على Phase 271 للعقود الأساسية.
- لا تكرر منطق replay في Phase 270.
- تحافظ على فصل Document/List/Report/Operational Shells.
- تمهد لمرحلة لاحقة يمكن فيها إضافة UI smoke runner أو CI server route probe.
