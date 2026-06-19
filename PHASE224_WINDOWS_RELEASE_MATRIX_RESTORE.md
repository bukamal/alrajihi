# Phase 224 — Windows Release Matrix Restore

## الهدف
استعادة مصفوفة بناء Windows Release بحيث لا ينتج الـ workflow مخرجين فقط، بل يرجع ينتج أربع حزم واضحة:

- `AlrajhiAccounting_Release_Portable`
- `AlrajhiAccounting_Release_Installer`
- `AlrajhiAccountingWarehouse_Release_Portable`
- `AlrajhiAccountingWarehouse_Release_Installer`

## الملفات المعدلة

- `.github/workflows/build-windows-installer.yml`
- `build/build_windows.ps1`
- `build/pyinstaller_hidden_imports.py`
- `tools/release_packaging_guard.py`
- `tools/phase224_windows_release_matrix_guard.py`

## PyInstaller

تم تحويل أمر PyInstaller في الـ workflow إلى مصفوفة PowerShell args بدل backtick command طويل، لتقليل أخطاء escape/continuation في GitHub Actions.

تم تضمين مجلد assets كاملًا في النسخة المحمولة بمسارين:

- `alrajhi_client\assets;assets`
- `alrajhi_client\assets;alrajhi_client\assets`

وهذا يحافظ على أيقونات وشعارات المشروع داخل portable build، سواء وضعها PyInstaller مباشرة في مجلد التطبيق أو داخل `_internal`.

تم أيضًا تحديث hidden imports للوثائق/التبويبات الجديدة التي أضيفت في المراحل الأخيرة، مثل:

- `features.finance.documents.expense_document_tab`
- `features.finance.documents.cashbox_document_tab`
- `features.finance.documents.bank_account_document_tab`
- `features.branches.documents.branch_document_tab`
- `features.inventory.documents.warehouse_document_tab`
- `features.inventory.documents.inventory_transfer_document_tab`
- `features.users.documents.user_document_tab`
- `features.transactions.transaction_document_tab`
- `features.transactions.documents.*`

## Inno Setup

تم إنشاء ملفي Inno مستقلين أثناء CI:

- `setup_release.iss`
- `setup_warehouse_release.iss`

الأول يبني Release عام باسم:

- `AlrajhiAccounting_Release_Setup.exe`

والثاني يبني Warehouse Release باسم:

- `AlrajhiAccountingWarehouse_Release_Setup.exe`

كلاهما يستخدم:

- `alrajhi_client\assets\brand\app.ico`
- `SetupIconFile`
- `UninstallDisplayIcon`
- `IconFilename`

## Artifacts

تم استبدال upload القديم ذي المخرجين فقط بأربع خطوات upload مستقلة:

- `AlrajhiAccounting_Release_Installer`
- `AlrajhiAccounting_Release_Portable`
- `AlrajhiAccountingWarehouse_Release_Installer`
- `AlrajhiAccountingWarehouse_Release_Portable`

## Guard

تمت إضافة:

- `tools/phase224_windows_release_matrix_guard.py`

ويتحقق من وجود الأربع artifacts، وملفي Inno، وربط الأيقونات، وتضمين assets كاملة، وعدم رجوع نمط upload القديم الذي كان ينتج مخرجين فقط.

## الفحوص

- `python tools/phase224_windows_release_matrix_guard.py`
- `python tools/verify_branding_assets.py`
- `python tools/release_packaging_guard.py`
- `python tools/release_hidden_imports_guard.py`
- `python tools/phase223_finance_list_legacy_cleanup_guard.py`
- `python tools/phase222_expense_document_shell_guard.py`
- `python tools/phase221_voucher_document_shell_guard.py`
- `python tools/phase220_party_document_shell_guard.py`
- `python tools/phase219_projectwide_architecture_audit.py`
- `python tools/reports_contract_check.py`
- `python tools/phase212_runtime_stabilization_guard.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
