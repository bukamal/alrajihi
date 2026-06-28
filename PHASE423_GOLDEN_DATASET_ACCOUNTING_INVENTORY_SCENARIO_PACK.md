# Phase 423 — Golden Dataset Accounting & Inventory Scenario Pack

## هدف المرحلة

هذه المرحلة تضيف مجموعة بيانات معيارية ثابتة للتحقق من الحسابات والمخزون والتقارير دون الاعتماد على واجهة Qt أو قاعدة بيانات تشغيلية. الهدف هو أن يكون لدى المشروع مرجع حسابي واضح يثبت أن الفواتير والمرتجعات والتحويلات والتصنيع وPOS والمطعم والسندات تؤدي إلى أرصدة متوقعة ومعلنة.

## ما تم إضافته

- `alrajhi_client/workspace/quality/golden_dataset_scenarios_contract.py`
- `alrajhi_client/workspace/quality/golden_dataset_scenarios.py`
- `tools/phase423_golden_dataset_scenarios_guard.py`
- `tests/test_phase423_golden_dataset_scenarios.py`
- `tools/audit_outputs/golden_dataset_scenarios_matrix.csv`
- `tools/audit_outputs/golden_dataset_expected_balances.json`
- `tools/audit_outputs/golden_dataset_operations.json`

## السيناريوهات المغطاة

- بيانات أساسية: فروع، مستودعات، صناديق، عملاء، موردون، مواد.
- أرصدة افتتاحية.
- فاتورة شراء.
- فاتورة بيع.
- مرتجع بيع.
- مرتجع شراء.
- تحويل مستودع بين فرعين.
- أمر تصنيع BOM/Production.
- بيع POS نقدي.
- طلب مطعم نقدي مع استهلاك مكونات.
- سند قبض.
- سند دفع.
- سند مصروف.
- نقطة قطع للتقارير.

## النتائج الذهبية الأساسية

- النقد الكلي: `1285.75 SYP`
- ذمة العميل: `272.50 SYP`
- ذمة المورد: `349.00 SYP`
- صافي المبيعات: `865.00 SYP`
- تكلفة المبيعات: `400.00 SYP`
- مجمل الربح: `465.00 SYP`
- ضريبة مستحقة/رصيد ضريبي: `-20.75 SYP`
- تكلفة التصنيع: `200.00 SYP`

## أرصدة المخزون النهائية

- `MAT-RAW@WH-MAIN = 10.0000`
- `MAT-RETAIL@WH-MAIN = 3.0000`
- `MAT-RETAIL@WH-BR2 = 1.0000`
- `MAT-FINISHED@WH-MAIN = 1.0000`

## حدود المرحلة

هذه المرحلة لا تعيد تشغيل السيناريو ضد قاعدة بيانات الإنتاج. هي تضيف مرجعًا ذهبيًا مستقلًا يمكن لاحقًا في مرحلة Runtime Replay مقارنته مع نتائج DAO والتقارير الفعلية. هذا مقصود حتى تبقى المرحلة قابلة للتشغيل في CI وبيئات لا تحتوي PyQt أو قاعدة بيانات كاملة.

## طريقة التشغيل

```bash
python tools/phase423_golden_dataset_scenarios_guard.py
pytest -q tests/test_phase423_golden_dataset_scenarios.py
```
