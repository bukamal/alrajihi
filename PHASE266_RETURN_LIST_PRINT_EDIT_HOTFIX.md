# PHASE266_RETURN_LIST_PRINT_EDIT_HOTFIX

## الهدف

إصلاح طباعة مرتجعات المبيعات ومرتجعات المشتريات من داخل واجهات قوائم المرتجعات نفسها، وإضافة فتح مستند تعديل المرتجع عند النقر المزدوج على صف القائمة.

## المشكلة

كانت قوائم المرتجعات تعرض المبالغ بعملة العرض، مثل SYP/ل.س، لكنها عند الطباعة كانت تجلب المرتجع من الخدمة وتدفع القيم المخزنة داخليًا إلى قالب الطباعة مباشرة. القيم المخزنة تاريخيًا تكون بعملة التخزين/الأساس، غالبًا USD، لذلك كانت الطباعة تعرض أرقامًا مثل 2.14 مع رمز ل.س بدل 30,000.00 ل.س.

كذلك لم يكن النقر المزدوج على صف مرتجع البيع أو الشراء مضمونًا لفتح مستند التعديل الرسمي.

## التعديلات

### returns_widget.py

أضيفت دالة:

`_ret_list_return_print_payload(raw_return, row_data=None, qty_kind='sale')`

تقوم بما يلي:

- تحويل مبالغ المرتجع المخزنة من `currency.storage_currency()` إلى `currency.get_display_currency()` قبل الطباعة.
- تحويل `unit_price`, `line_total`, `total`, `refund_amount`, `credit_amount` إلى عملة العرض.
- تمرير مفاتيح العملة صراحة إلى قالب الطباعة:
  - `display_currency`
  - `currency`
  - `currency_code`
  - `document_currency`
- استخدام بيانات الصف المعروض لتكميل اسم العميل/المورد ورقم الفاتورة الأصلية عندما لا يعيد `get()` هذه القيم.
- تفضيل `return_no` كرقم مطبوع بدل السقوط إلى `id` فقط.

تم تعديل:

- `ReturnsWidget.print_selected_return`
- `PurchaseReturnsWidget.print_selected_return`

ليستخدما payload الطباعة الجديد بدل تمرير البيانات الخام مباشرة.

أضيف ربط النقر المزدوج:

- `ReturnsWidget.table.doubleClicked -> edit_return_from_index`
- `PurchaseReturnsWidget.table.doubleClicked -> edit_return_from_index`

مع دعم الجداول المفلترة عبر `selected_source_rows()` و `proxy.mapToSource()`.

### print_templates.py

- أصبح `return_html()` يفضّل `return_no` ضمن رقم المستند.
- تمت إضافة mapping لطريقة الدفع `credit_only` إلى `payment_credit` حتى لا تظهر في الطباعة كقيمة إنكليزية خام.

## النتيجة

طباعة المرتجع من قائمة مرتجعات المبيعات/المشتريات تحترم العملة المعروضة في الواجهة، ولا تطبع قيمة USD خامًا مع رمز العملة المحلية.

النقر المزدوج على صف مرتجع يفتح مستند تعديل المرتجع الرسمي عبر `MainWindow.open_return_document(...)`، مع fallback إلى الـ dialog القديم فقط عند عدم وجود MainWindow/TabbedWorkspace.

## الفحص

- `compileall`: ناجح.
- `pytest -q`: `226 passed`, `1 warning`.
