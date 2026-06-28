# Phase 416 — Runtime Acceptance Harness

## الهدف

Phase 416 لا تضيف ميزة جديدة للمستخدم. هذه مرحلة تشخيص وتشغيل قبول Runtime مخصصة لإغلاق الفجوة بين نجاح الـ static guards وبين ظهور خلل فعلي داخل واجهة Qt، خصوصًا:

- أثر شريط القوائم في الزاوية اليسارية العليا.
- سلوك Enter داخل الجداول التحريرية.
- اختلاف RTL/LTR عند تغيير اللغة.
- حفظ التفضيلات وسلوك النوافذ عند التشغيل الحقيقي.

## ما أضيف

- `alrajhi_client/workspace/runtime/runtime_acceptance_harness.py`
- `alrajhi_client/workspace/quality/runtime_acceptance_harness_contract.py`
- `tools/phase416_runtime_acceptance_harness_guard.py`
- `tools/run_phase416_runtime_acceptance.py`
- `tests/test_phase416_runtime_acceptance_harness.py`

## طبيعة الاختبار

الحزمة تعمل بطبقتين:

1. طبقة import-safe بدون PyQt5:
   - تكتب مصفوفة السيناريوهات.
   - تتحقق من وجود hooks الخاصة بالـ Runtime.
   - تعمل داخل CI/headless environments.

2. طبقة Qt Runtime عند توفر PyQt5:
   - تفتح `MainWindow` فعليًا.
   - تلتقط QWidget tree مع `objectName`, class, visible, geometry, layoutDirection.
   - تحفظ screenshot للشريط في العربية RTL والألمانية/الإنكليزية LTR.
   - تشغّل QTest على Sales Invoice Grid للتحقق من Enter وعدم مسح القيم وعدم إنشاء أكثر من صف فارغ.

## تشغيل يدوي على جهاز التطوير

من جذر المشروع:

```bash
python tools/run_phase416_runtime_acceptance.py --output-dir tools/audit_outputs/runtime_acceptance
```

لإنشاء مصفوفة السيناريوهات فقط دون فتح Qt:

```bash
python tools/run_phase416_runtime_acceptance.py --matrix-only
```

## المخرجات

- `tools/audit_outputs/runtime_acceptance_harness_matrix.csv`
- `tools/audit_outputs/runtime_acceptance_scenario_matrix.csv`
- عند تشغيل Qt Runtime:
  - `tools/audit_outputs/runtime_acceptance/shell_widget_tree_ar.csv`
  - `tools/audit_outputs/runtime_acceptance/shell_snapshot_ar.png`
  - `tools/audit_outputs/runtime_acceptance/shell_widget_tree_de.csv`
  - `tools/audit_outputs/runtime_acceptance/shell_snapshot_de.png`
  - `tools/audit_outputs/runtime_acceptance/sales_invoice_enter_probe.json`
  - `tools/audit_outputs/runtime_acceptance/runtime_acceptance_probe_summary.json`

## معيار القبول

- يجب أن يظهر `CleanShellNavigationBar` مرة واحدة فقط.
- يجب ألا يظهر `ModernTopBar` أو `IconMenuBar` أو `MainNavToolButton` كعناصر مرئية.
- يجب ألا توجد عناصر مرئية غير مفسرة في الزاوية العليا اليسرى.
- Enter داخل فاتورة البيع يجب ألا يمسح قيمة موجودة.
- Enter في نهاية الصف يجب ألا ينشئ أكثر من صف فارغ واحد.
- عند إخفاء الأعمدة، يجب أن يتبع التنقل الأعمدة المرئية والمسار التجاري، لا ترتيب Qt الفيزيائي فقط.

## ملاحظة مهمة

في بيئة لا تحتوي PyQt5، تمر المرحلة كـ contract/static harness فقط. الحكم النهائي على خلل الرسم والتنقل يحتاج تشغيل الأمر أعلاه على الجهاز الذي تظهر عليه المشكلة.
