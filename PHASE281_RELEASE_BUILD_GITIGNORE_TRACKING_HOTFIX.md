# Phase 281 — Release Build Gitignore Tracking Hotfix

## الهدف

إصلاح فشل CI عند تشغيل:

```bash
python tools/release_packaging_guard.py
```

بسبب غياب ملفات `build/pyinstaller_hidden_imports.py` و hooks داخل بيئة GitHub Actions.

## السبب

كانت `.gitignore` تحتوي على النمط:

```gitignore
build/
```

وهذا يجعل Git يتجاهل ملفات build المطلوبة للإصدار، حتى لو كانت موجودة داخل ZIP المحلي. النتيجة: عند checkout في CI تكون الملفات غير موجودة، فتفشل حراس release packaging و Windows runtime packaging.

## التغيير

تم استبدال تجاهل `build/` الكامل بتجاهل مخرجات build فقط، مع إبقاء ملفات عقد الإصدار قابلة للتتبع:

- `build/build_windows.ps1`
- `build/setup.iss`
- `build/pyinstaller_hidden_imports.py`
- `build/hooks/*.py`

كما تم تحديث حارس release packaging وحارس Windows packaging للتحقق من أن `.gitignore` لا يمنع تتبع هذه الملفات.

## التحقق

تم تشغيل:

```bash
python tools/release_packaging_guard.py
python tools/release_hidden_imports_guard.py
python tools/windows_runtime_packaging_gate_audit.py
python tools/release_readiness_gate_audit.py
python tools/phase32_invoice_flow_guard.py
```

كلها تمر بدون أخطاء.
