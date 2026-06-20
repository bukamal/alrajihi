# PHASE 280 — Release Packaging Guard Cleanup Hotfix

## الهدف

إصلاح فشل CI في مسار `tools/release_packaging_guard.py` و `tools/release_hidden_imports_guard.py` و `tools/windows_runtime_packaging_gate_audit.py` بعد مراحل توحيد Windows/PyInstaller.

## المشكلة

ظهر الفشل بسبب ثلاث نقاط:

1. بعض بيئات CI تولد مجلدات `__pycache__` و `.pytest_cache` قبل تشغيل `release_packaging_guard.py`، فيتعامل معها الحارس كأنها ملفات release ملوثة.
2. `alrajhi_client/printing/_template_loader.py` احتوى تعبير f-string غير متوافق مع Python 3.11 عند سطر fallback الخاص بـ `no_data`.
3. `release_hidden_imports_guard.py` كان يتعامل مع `flask_jwt_extended` كأنه ملف داخلي يجب أن يوجد داخل المستودع، مع أنه dependency خارجي.

## الإصلاح

- أصبح `release_packaging_guard.py` ينظف cache artifacts الناتجة عن خطوات CI قبل الحكم على الحزمة.
- تم إصلاح f-string في `_fallback_report_template` داخل `_template_loader.py` عبر احتساب `no_data_text` خارج الـ f-string.
- أصبح `release_hidden_imports_guard.py` يسمح بالـ hidden imports الخارجية المعروفة مثل `flask_jwt_extended` دون البحث عن ملف محلي لها.
- تم توسيع Release Readiness Gate ليشمل Phase 279 و Phase 280 وحارسي release packaging/hidden imports.

## التحقق

الأوامر التي يجب أن تمر:

```bash
python tools/release_packaging_guard.py
python tools/release_hidden_imports_guard.py
python tools/windows_runtime_packaging_gate_audit.py
python tools/release_readiness_gate_audit.py
python tools/phase32_invoice_flow_guard.py
```

## ملاحظة

الـ ZIP النهائي يجب أن يبقى خاليًا من `__pycache__` و `.pytest_cache`، حتى لو أصبحت أداة الحراسة تنظفها تلقائيًا قبل الفحص.
