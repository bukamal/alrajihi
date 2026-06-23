# Phase 369 — Warehouse Installer & Printing Paths

## الهدف

تثبيت مسار إصدار Windows بحيث ينتج البناء حزمة واحدة فقط:

- `AlrajhiAccountingWarehouse_Release_Installer`

وإلغاء نشر أي مخرجات Portable أو Generic Accounting Release، مع إعادة حماية مسارات الطباعة داخل النسخة المثبتة.

## التغييرات

- تحديث `.github/workflows/build-windows-installer.yml` لنشر artifact واحد فقط باسم `AlrajhiAccountingWarehouse_Release_Installer`.
- تحديث `build/setup.iss` ليولد `AlrajhiAccountingWarehouse_Release_Setup.exe` ويثبت إلى مجلد `AlrajhiAccountingWarehouse`.
- إبقاء PyInstaller staging باسم `AlrajhiAccounting` حتى لا تنكسر مسارات التشغيل والبيانات التاريخية داخل التطبيق.
- تحديث `build/build_windows.ps1` للتحقق من وجود ملفات الطباعة داخل staging installer source:
  - `print_templates.py`
  - `_template_loader.py`
- تحديث `printing_service` و `_template_loader` للبحث عن قوالب الطباعة داخل:
  - مجلد الوحدة الحالي.
  - `cwd`.
  - `sys._MEIPASS`.
  - `_internal` داخل `sys._MEIPASS`.
  - مجلد exe.
  - `_internal` بجانب exe.
- تحسين فتح HTML للطباعة عبر `QDesktopServices.openUrl(QUrl.fromLocalFile(...))` مع fallback إلى `webbrowser` ثم `os.startfile` على Windows.

## الحارس والاختبارات

- `tools/phase369_warehouse_installer_printing_guard.py`
- `tests/test_phase369_warehouse_installer_printing.py`
- `alrajhi_client/workspace/quality/warehouse_installer_printing_contract.py`
