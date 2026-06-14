# GATEWAY PHASE 70 — Stable Table/Tab QSS Only Hotfix

## الهدف
الرجوع إلى نسخة Phase 65 المستقرة التي كانت تعمل، مع تطبيق تحسينات الجداول والتبويبات بطريقة آمنة عبر QSS فقط.

## التشخيص
- سبب التعطل لم يكن Design System الأساسي في Phase 65.
- الخطر بدأ بعد Phase 66 بسبب طبقة Runtime Polish العامة التي ركّبت EventFilter على كامل التطبيق وتفحص كل Widgets أثناء Show/ChildAdded/Polish.
- Phase 68 أضاف إعدادات Qt/Chromium غير مناسبة لبيئة Linux/root وسببت رسائل `--shm-helper`.

## ما تم فعله
- استخدام Phase 65 كنقطة أساس مستقرة.
- عدم إضافة `widget_polish.py`.
- عدم تركيب EventFilter عام.
- عدم إضافة أي متغيرات QtWebEngine/Chromium.
- توسيع QSS فقط ليشمل:
  - QTableView
  - QTableWidget
  - QTreeView
  - QTreeWidget
  - QTabWidget/QTabBar
  - عناصر الجداول والصف المحدد والـ scrollbars

## الاختبارات
- compileall: PASS
- build_global_qss(light): PASS
- build_global_qss(dark): PASS
- grep for widget_polish/install_design_system_polish/QTWEBENGINE/shm-helper: CLEAN

## ملاحظة تشغيلية
هذه النسخة لا تستخدم Runtime auto-polish، وبالتالي أكثر أمانًا من Phase 66/67/68 على Linux وWindows.
