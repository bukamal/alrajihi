# Phase 371 — Reused Windows Workflow, Warehouse-Only

## الهدف

إعادة استخدام بنية ملف GitHub Actions الكامل الذي كان يحتوي خطوات التحقق والبناء التفصيلية، مع إبقاء سياسة الإصدار الجديدة: إصدار Warehouse فقط، بدون Accounting Release وبدون Portable artifacts.

## ما تم اعتماده من الملف القديم

- التشغيل على `push` إلى `main/master` و `workflow_dispatch`.
- تثبيت Python 3.10.
- ترقية pip وتثبيت المتطلبات و PyInstaller.
- التحقق من requirements.
- التحقق من imports الحرجة.
- التحقق من بنية المشروع والهوية.
- نسخ DLLs الخاصة بـ pyzbar.
- اكتشاف Qt platforms.
- تشغيل release hardening guards قبل البناء.
- تحميل Inno Setup واللغة العربية.
- إنشاء Inno script داخل workflow.
- بناء المثبت ورفعه كـ artifact.

## ما تم تغييره عمدًا

- تم منع `AlrajhiAccounting_Release_Installer`.
- تم منع كل Portable artifacts.
- تم منع `AlrajhiAccounting_Release_Setup.exe`.
- أصبح المسار الوحيد:
  - `dist\AlrajhiAccountingWarehouse`
  - `AlrajhiAccountingWarehouse.exe`
  - `AlrajhiAccountingWarehouse_Release_Setup.exe`
  - `AlrajhiAccountingWarehouse_Release_Installer`

## حماية الطباعة

الـ workflow يتحقق من وجود:

- `print_templates.py`
- `_template_loader.py`

داخل مسارات Warehouse dist، بما في ذلك `_internal` ومسار `alrajhi_client`، حتى لا تتوقف الطباعة داخل النسخة المثبتة.

## الحارس

- `tools/phase371_reused_windows_workflow_guard.py`
- `alrajhi_client/workspace/quality/reused_windows_workflow_contract.py`

