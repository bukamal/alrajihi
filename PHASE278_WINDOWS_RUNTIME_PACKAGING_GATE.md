# Phase 278 — Windows Runtime Packaging Gate

## الهدف

هذه المرحلة تضيف حارسًا صريحًا لمسار بناء Windows / PyInstaller حتى لا تتكرر أخطاء التشغيل التي ظهرت سابقًا في النسخة التنفيذية، مثل:

- نقص `printing._template_loader` داخل الحزمة.
- وجود `print_templates.py` كملف data لكنه يحتوي SyntaxError لا يكتشف إلا عند الطباعة.
- نسيان `hidden-import` أو `collect-submodules` بعد إضافة وحدات جديدة.
- خروج build ناجح ظاهريًا لكنه ناقص قوالب الطباعة داخل `_internal` أو مسارات `printing`.

## الملفات الجديدة

- `alrajhi_client/workspace/packaging/windows_packaging_gate_contract.py`
- `tools/windows_runtime_packaging_gate_audit.py`
- `tests/test_phase278_windows_runtime_packaging_gate.py`

## ما يتم فحصه

الحارس يفحص دون PyQt ودون تشغيل التطبيق:

- وجود ملفات التشغيل الحرجة.
- سلامة syntax في `print_templates.py`, `_template_loader.py`, `printing_service.py`, وملفات migrations.
- تطابق `build/pyinstaller_hidden_imports.py` مع `build/build_windows.ps1` و GitHub workflow.
- تضمين `printing` و `alrajhi_client.printing` كـ `collect-data` و `collect-submodules`.
- وجود `--add-data` صريح لـ `print_templates.py` و `_template_loader.py` تحت المسارين.
- أن hooks تجمع submodules وتُدخل ملفات Python نفسها عبر `include_py_files=True`.
- أن build المحلي و CI يشغلان الحارس قبل PyInstaller.
- أن build بعد PyInstaller يفشل إذا لم يجد `print_templates.py` و `_template_loader.py` داخل مجلد `dist`.

## العلاقة مع Phase 277

تم إدخال فحص Phase 278 ضمن `Release Readiness Gate` حتى يظهر في مصفوفة الجاهزية العامة ولا يبقى فحص Windows منفصلًا عن باقي عقود المشروع.

## نتيجة التنفيذ

الحارس يعطي مخرجات:

- `tools/audit_outputs/windows_runtime_packaging_gate_matrix.csv`
- `tools/audit_outputs/windows_runtime_packaging_gate_summary.json`


## استقرار مسار الاختبارات

أضيف `tests/conftest.py` لضبط `sys.path` أثناء الاختبارات بحيث تعمل الصيغتان معًا:

- `alrajhi_client.*` للتشغيل package-qualified.
- `printing.*`, `features.*`, `workspace.*` لنمط PyInstaller الذي يضع `alrajhi_client` على مسار البحث.

هذا يمنع اختلاف نتائج الاختبارات بين التشغيل الجزئي، التشغيل الكامل، وبيئة CI.
