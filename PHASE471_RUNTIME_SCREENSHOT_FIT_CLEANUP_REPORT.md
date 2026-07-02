# PHASE471 — Runtime Screenshot Fit Cleanup

## الهدف
معالجة الملاحظات المرئية من صور التشغيل الفعلية بعد Phase470: تزاحم رأس فواتير البيع/الشراء، احتمال قص أزرار الفوتر، تكرار/ثقل زر Excel في قوائم العرض، وقص إجمالي المطعم داخل فوتر ضيق.

## التعديلات

### 1. فواتير البيع والشراء
- تحويل رأس المستند إلى ثلاث طبقات مستقرة:
  - صف البيانات: العميل/المورد، التاريخ، المستودع، العملة، المرجع.
  - صف البحث: البحث عن مادة/باركود، إضافة، + مادة.
  - صف الأدوات: نمط العرض، الأعمدة، إعادة الضبط، حفظ.
- تحويل كبسولات الحقول إلى label-over-control بدل label بجانب control لمنع قص النصوص العربية.
- توسيع الحدود القصوى لحقول التاريخ والمستودع والمرجع والطرف.

### 2. أزرار أسفل الفاتورة
- الإبقاء على Grid responsive.
- ضبط أبعاد الأزرار لتكون قابلة للتمدد داخل الخلايا بدل التداخل.

### 3. فوتر المطعم
- إعطاء إجمالي المطعم صفًا كاملًا مستقلًا.
- وضع أزرار الطباعة/الدفع في صف منفصل.
- تقليل حجم خط الإجمالي حتى لا يُقص في العمود الضيق.

### 4. قوائم الجداول
- تغيير زر التصدير المرئي إلى `Excel` فقط، مع إبقاء tooltip `export_excel`.
- الهدف منع ظهور نصوص طويلة أو مكررة مثل "تصدير تصدير Excel".

## الملفات المعدلة
- `alrajhi_client/features/transactions/transaction_document_tab.py`
- `alrajhi_client/features/transactions/components/transaction_bottom_actions.py`
- `alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py`
- `alrajhi_client/views/widgets/components/table_toolbar.py`
- `alrajhi_client/theme/qss.py`
- `tests/test_phase471_runtime_screenshot_fit_cleanup.py`

## التحقق
- compileall
- architecture_guard
- i18n/RTL guard
- Phase471 tests
- selected visual/runtime contract tests
