# Phase 271 — End-to-End Scenario Guard Matrix

## الهدف

بعد توحيد Document Shell و List Workspace و Report Shell و Operational Shell، أصبحت الحاجة العملية هي التأكد من أن سيناريوهات العمل الكاملة لا تعتمد على انطباع عام، بل على مصفوفة حراسة قابلة للفحص.

هذه المرحلة تضيف عقدًا يربط كل سيناريو عمل كامل مع:

- الواجهة المالكة للسيناريو.
- API/network path.
- RBAC permission.
- branch policy.
- currency policy.
- settings scope.
- i18n scope.
- print/export behavior.
- audit event.
- offline/replay behavior عند اللزوم.

## الملفات المضافة

- `alrajhi_client/workspace/scenarios/scenario_guard_contract.py`
- `alrajhi_client/workspace/scenarios/__init__.py`
- `tools/end_to_end_scenario_guard_audit.py`
- `tests/test_phase271_end_to_end_scenario_guard_matrix.py`

## السيناريوهات المحمية

- دورة فاتورة بيع.
- دورة فاتورة شراء.
- تعديل وطباعة مرتجع بيع.
- تعديل وطباعة مرتجع شراء.
- POS fast sale + thermal receipt.
- مطعم: جلسة، مطبخ، دفع، طباعة إيصال.
- BOM / تركيبة تصنيع + تكلفة وطباعة.
- أمر إنتاج + طباعة وتقرير.
- تحويل مخزني + طباعة وتقرير حركة.
- سند قبض/دفع + طباعة وتقرير حركة نقدية.
- مادة + باركود/ملصق.
- تقرير قائمة الدخل مع طباعة وتصدير.

## المخرجات

الأداة:

```bash
python tools/end_to_end_scenario_guard_audit.py
```

تنتج:

- `tools/audit_outputs/end_to_end_scenario_guard_matrix.csv`
- `tools/audit_outputs/end_to_end_scenario_summary_matrix.csv`

## ملاحظة تصميمية

هذه المرحلة لا تنفذ UI smoke test لأنها يجب أن تعمل في CI و PyInstaller analysis بدون PyQt. الهدف هو منع فجوات العقود: سيناريو يملك واجهة لكنه بلا صلاحية، أو بلا audit، أو يطبع بلا currency policy، أو يعتمد على offline queue بلا replay contract.
