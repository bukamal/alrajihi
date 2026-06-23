# Phase373 — Tab Plain Title

## الهدف
إزالة الكلمات الظاهرة `رئيسي` و`فرعي` من عناوين التبويبات، مع الحفاظ على نوع التبويب داخليًا لأغراض دورة الحياة، الإغلاق، والتمييز التشغيلي.

## التغيير
- أصبح نص التبويب المرئي هو عنوان العمل فقط.
- أصبح tooltip هو عنوان العمل فقط.
- بقي `kind` و`tab_kind` داخل metadata بقيم `main/sub` غير مرئية.
- لم يتم تغيير سياسة لوحة التحكم: ما تزال سطحًا ثابتًا وليست تبويبًا.

## الملفات
- `alrajhi_client/shell/tab_label_policy.py`
- `alrajhi_client/workspace/quality/tab_plain_title_contract.py`
- `tools/phase373_tab_plain_title_guard.py`
- `tests/test_phase373_tab_plain_title.py`

## التحقق
- يجب أن يعرض `compose_tab_label('sales_invoices', 'فواتير البيع').display_text` القيمة `فواتير البيع` فقط.
- يجب أن يعرض `compose_tab_label('invoice:sale:new', 'فاتورة بيع جديدة').display_text` القيمة `فاتورة بيع جديدة` فقط.
- يجب أن تبقى `kind` متاحة كـ `main/sub` في metadata.
