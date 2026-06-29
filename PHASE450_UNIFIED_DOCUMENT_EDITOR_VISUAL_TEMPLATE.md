# Phase 450 — Unified Document Editor Visual Template

## الهدف

توحيد الهوية البصرية لمحررات المستندات التي بقيت بعد تطبيق الهوية على الـ Shell والقوائم وPOS والمطعم والتقارير.

تغطي هذه المرحلة:

- فواتير البيع والشراء والمرتجعات عبر `TransactionDocumentTab`.
- سندات القبض/الدفع عبر `VoucherEditorTab`.
- المصروفات.
- تحويلات المستودع.
- BOM وأوامر الإنتاج.
- محررات العميل/المورد والتصنيفات والإعدادات المستندية.

## ما تم تغييره

تم تعزيز `workspace/documents/document_layout_policy.py` بدالة جديدة:

`_apply_document_visual_template()`

وتضيف metadata بصرية مركزية:

- `documentVisualTemplatePhase = 450`
- `visualWorkspaceType = document`
- `visualRole = document_editor_surface`
- `document_header`
- `document_card`
- `document_summary`
- `document_action_bar`
- `document_input`
- `document_table`
- `document_primary_action`
- `document_danger_action`

تمت إضافة Tokens مركزية في `theme/brand.py` وقواعد QSS مركزية في `theme/qss.py` حتى لا تحتاج محررات المستندات إلى `setStyleSheet()` محلي.

## تنظيف آمن

تم إيقاف local QSS blocks في محررات مستندية بارزة، واستبدالها بعلامة:

`documentLocalStylesSuppressed = True`

الهدف منع أن تطغى التنسيقات القديمة على QSS المركزي.

## حدود المرحلة

لم يتم تغيير:

- منطق Enter في الجداول.
- الحفظ.
- الطباعة.
- الحسابات.
- المخزون.
- الصلاحيات.
- API/DAO.

المرحلة بصرية وتنظيمية فقط.
