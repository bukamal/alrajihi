# Phase 412 — Editable Grid Navigation Engine

## الهدف

هذه المرحلة تعالج خلل التنقل داخل الجداول التحريرية في المشروع ككل، وخصوصًا عند الضغط على Enter داخل فواتير البيع والشراء والمرتجعات وجداول التحويلات والتصنيع. المشكلة كانت ناتجة عن تعارض أكثر من طبقة: محرك تنقل مركزي، فلتر محلي داخل الفاتورة القديمة، delegates تقوم بالـ commit أثناء تحميل المحرر، وإضافة صفوف فارغة من أكثر من مسار.

## ما تم تغييره

- أصبح `StandardTableKeyboardMixin` هو المالك المركزي لسلوك Enter و Shift+Enter في الجداول التحريرية.
- تم تعطيل مسار Enter المحلي داخل `invoice_dialog.py` بحيث يترك الحدث إلى `TransactionLineGrid` بدل استعمال `_move_to_next_invoice_cell` المبني على أرقام أعمدة ثابتة.
- أضيف قفل إعادة دخول `_standard_enter_navigation_active` حتى لا يعالج Enter مرتين بسبب `eventFilter + closeEditor`.
- أضيف قفل إضافة الصف `_standard_enter_append_guard` حتى لا تنشأ عدة صفوف عند نهاية الصف.
- أضيفت قاعدة واحدة لإضافة الصف الأخير:
  - إذا كان يوجد صف فارغ في النهاية، يعاد استخدامه.
  - إذا لا يوجد، ينشأ صف واحد فقط.
  - إذا وجدت صفوف فارغة متعددة في النهاية، يتم تقليمها إلى صف واحد.
- تم منع `TransactionItemDelegate` من مسح قيمة مادة موجودة عند Enter إذا لم يعدّل المستخدم النص فعليًا.
- تم تعديل `ItemComboDelegate` في الفاتورة القديمة حتى لا ينفذ `commitData` من `currentIndexChanged` أثناء تحميل بيانات المحرر.
- تم توسيع المسارات الدلالية للتنقل لتغطي:
  - البيع والشراء.
  - المرتجعات.
  - تحويلات المستودع.
  - BOM/التصنيع.

## قاعدة القبول

عند الضغط على Enter داخل أي جدول تحريري، يجب أن يحدث الآتي:

1. الانتقال حسب ترتيب تجاري دلالي، لا حسب أرقام أعمدة ثابتة.
2. تجاهل الأعمدة المخفية.
3. عدم مسح محتوى الخلية لمجرد التنقل.
4. عدم إنشاء أكثر من صف فارغ واحد في نهاية الجدول.
5. Shift+Enter يرجع للخلف بنفس منطق المسار.
6. الجداول القديمة والجديدة تستخدم نفس المحرك بدل وجود مسارات متعارضة.

## الملفات الأساسية

- `alrajhi_client/ui/table_keyboard_policy.py`
- `alrajhi_client/views/dialogs/invoice_dialog.py`
- `alrajhi_client/views/dialogs/invoice_delegates.py`
- `alrajhi_client/features/transactions/grids/transaction_item_delegate.py`
- `alrajhi_client/workspace/quality/editable_grid_navigation_engine_contract.py`
- `tools/phase412_editable_grid_navigation_engine_guard.py`
- `tests/test_phase412_editable_grid_navigation_engine.py`

## النطاق

هذه المرحلة لا تغيّر الحسابات، الأسعار، الضرائب، المخزون، أو الحفظ. التغيير محصور في سلوك التنقل والتحرير داخل الجداول. الهدف هو إنهاء التعارضات التي كانت تؤدي إلى تخطي أعمدة، مسح خلايا، أو إنشاء أكثر من صف عند نهاية السطر.
