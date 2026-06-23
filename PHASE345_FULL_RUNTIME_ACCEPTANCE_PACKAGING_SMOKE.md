# Phase 345 — Full Runtime Acceptance & Packaging Smoke

## الهدف

تثبيت طبقة قبول تشغيلية نهائية قبل الانتقال إلى تجربة EXE حقيقي وأجهزة الطباعة. هذه المرحلة لا تشغل واجهة PyQt داخل CI ولا ترسل أوامر إلى الطابعات؛ بل تجمع كل العقود التشغيلية الآمنة في مصفوفة واحدة وتفصل بوضوح بين ما تم التحقق منه آليًا وما يحتاج تجربة يدوية على جهاز العميل.

## ما تمت إضافته

- عقد قبول PyQt-free:
  - `alrajhi_client/workspace/quality/full_runtime_acceptance_contract.py`
- حارس قبول وتشغيل وتغليف:
  - `tools/phase345_full_runtime_acceptance_packaging_smoke.py`
- مخرجات تدقيق:
  - `tools/audit_outputs/full_runtime_acceptance_packaging_smoke_matrix.csv`
  - `tools/audit_outputs/full_runtime_acceptance_packaging_smoke_summary.json`
- اختبار:
  - `tests/test_phase345_full_runtime_acceptance_packaging_smoke.py`

## نطاق القبول الآلي

الحارس يتحقق آليًا من:

- تسجيل صفحات التشغيل الحرجة في سجل الواجهات.
- وجود عقود الأعمدة لكل المجالات الأساسية: الفواتير، POS، المطعم، الكافي، الألبسة، المستودعات، التصنيع، المالية، التقارير، الإعدادات.
- وجود بروفايلات الباركود وأنها Browser HTML فقط وتدعم الطباعة المتعددة حيث يلزم.
- وجود خطط smoke غير تدميرية للسيناريوهات التشغيلية.
- نجاح dry-run للسيناريوهات دون كتابة بيانات أعمال.
- جاهزية Windows packaging gate قبل بناء EXE.
- وجود ملفات الدخول والتغليف الأساسية.
- سلامة Release Gate بعد إضافة هذه المرحلة.

## نطاق القبول اليدوي الصريح

هذه البنود تظهر في المصفوفة كـ `manual_required` ولا تُعامل كفشل آلي:

- تشغيل EXE الحقيقي على جهاز Windows نظيف.
- طباعة A4 للفواتير والتقارير.
- طباعة إيصالات حرارية لـ POS/المطعم/الكافي.
- طباعة لصاقات باركود للمواد/الألبسة/المطعم/الكافي.
- تشغيل Remote/API مع أكثر من مستخدم وفرع ومستودع وصندوق.
- تجربة ترقية قاعدة بيانات قديمة ثم النسخ الاحتياطي والاسترجاع.

## أوامر التحقق

```bash
python tools/phase345_full_runtime_acceptance_packaging_smoke.py
pytest -q tests/test_phase345_full_runtime_acceptance_packaging_smoke.py
```

## النتيجة

هذه المرحلة تجعل حالة القبول واضحة: ما تم إثباته آليًا، وما يحتاج تجربة جهاز/شبكة/طابعة فعلية قبل التسليم النهائي.
