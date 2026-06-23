# Phase 370 — Warehouse Executable Identity

## المشكلة

مرحلة Phase 369 وحّدت اسم artifact واسم installer، لكنها أبقت PyInstaller وملف التشغيل المثبت باسم `AlrajhiAccounting.exe`. لذلك يمكن أن تظهر نتيجة البناء للمستخدم كنسخة Accounting عامة بدل Warehouse، حتى لو كان اسم artifact على GitHub صحيحًا.

## القرار

يجب أن تكون هوية Warehouse ممتدة من أول البناء إلى آخر ملف مثبت:

- اسم artifact: `AlrajhiAccountingWarehouse_Release_Installer`.
- اسم ملف المثبّت: `AlrajhiAccountingWarehouse_Release_Setup.exe`.
- اسم مجلد PyInstaller: `dist/AlrajhiAccountingWarehouse`.
- اسم ملف التشغيل المثبت: `AlrajhiAccountingWarehouse.exe`.
- مصدر Inno Setup: `..\dist\AlrajhiAccountingWarehouse\*`.

## ما تم تعديله

- تحديث `build/build_windows.ps1` ليستخدم `$PyInstallerAppName = "AlrajhiAccountingWarehouse"`.
- تحديث فحص exe بعد PyInstaller ليبحث عن `$PyInstallerAppName.exe` بدل اسم Accounting ثابت.
- تحديث فحص ملفات الطباعة ليستخدم `$PyInstallerDistDir`، حتى تبقى الطباعة تعمل بعد تغيير اسم مجلد التوزيع.
- تحديث `build/setup.iss` ليثبت ويشغّل `AlrajhiAccountingWarehouse.exe` من `dist\AlrajhiAccountingWarehouse`.
- إزالة أسماء generic Accounting release من release scripts الفعلية.
- تحديث guards الخاصة بـ Windows packaging وPhase 224/369.
- إضافة guard جديد Phase 370 لمنع عودة هذا الخلل.

## النتيجة المتوقعة

البناء القادم لن ينتج أو يرفع Accounting Release أو Portable. الناتج الوحيد هو Warehouse installer، والملف المثبت داخله يحمل اسم Warehouse أيضًا.
