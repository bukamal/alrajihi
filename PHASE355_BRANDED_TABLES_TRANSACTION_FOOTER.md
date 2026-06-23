# Phase 355 — Branded Tables & Transaction Footer

## الهدف
تطبيق الهوية البصرية المستوحاة من الشعار على الجداول، الخلية النشطة، ملخص الفاتورة، وأزرار أسفل المستندات بشكل موحد عبر فواتير البيع والشراء والمرتجعات والواجهات المشابهة.

## ما تم توحيده

- كل `CustomTableView` و `SmartTableView` يحصل على خاصية `brand_table_surface` حتى تطبق عليه طبقة QSS الموحدة.
- كل جدول تحريري يعمل بسياسة الإدخال الموحدة يحصل على `brand_entry_table` لتمييز الخلية الحالية بوضوح.
- رأس الجدول أصبح له ارتفاع وحدّ هوية واضح.
- الخلية الحالية داخل جدول التحرير أصبحت مميزة بخلفية وحدّ مشتقين من ألوان الهوية.
- `TransactionFooterPanel` وملخص الإجماليات والدفع تستخدم نفس ألوان وحجوم الهوية.
- أزرار أسفل الفواتير والمرتجعات أصبحت أكبر وأكثر وضوحًا، مع تمييز أزرار الحفظ والطباعة والإجراءات الأساسية.

## الملفات الأساسية

- `alrajhi_client/theme/table_identity.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/views/custom_table_view.py`
- `alrajhi_client/ui/table_keyboard_policy.py`
- `alrajhi_client/features/transactions/transaction_document_tab.py`
- `alrajhi_client/features/transactions/components/transaction_totals_panel.py`
- `alrajhi_client/features/transactions/components/transaction_bottom_actions.py`
- `tools/phase355_branded_tables_transaction_footer_guard.py`
- `tests/test_phase355_branded_tables_transaction_footer.py`

## الحارس

`tools/phase355_branded_tables_transaction_footer_guard.py` يتحقق من وجود tokens، QSS markers، و runtime markers المطلوبة بدون استيراد PyQt.
