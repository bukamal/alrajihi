# Phase 176 — POS Visual/Grid Unification

## الهدف

توحيد واجهة POS بصريًا وتقنيًا مع محرك الجداول الجديد، بعد أن تم في Phase 175 توحيد خط الباركود والوحدات والمخزون والإعدادات.

هذه المرحلة لا تغيّر منطق checkout أو إنشاء الفاتورة، بل تستبدل جدول السلة القديم داخل POS بمحرك grid/model موحد قابل للتوسعة للـ POS والمطعم لاحقًا.

## الملفات الجديدة

```text
alrajhi_client/features/pos/pos_line_schema.py
alrajhi_client/features/pos/pos_line_model.py
alrajhi_client/features/pos/pos_line_grid.py
tools/phase176_pos_visual_grid_guard.py
```

## الملفات المعدّلة

```text
alrajhi_client/views/widgets/pos_widget.py
alrajhi_client/features/pos/pos_preferences.py
alrajhi_client/i18n/translator.py
```

## ما تم توحيده

- POS لم يعد يستخدم `EditableSmartGrid` كسلة مبيعات يدوية.
- POS أصبح يستخدم `POSLineGrid` المبني على `TransactionLineGrid`.
- POS أصبح يستخدم `POSLineModel` المبني على `QAbstractTableModel` بدل ملء `QTableWidgetItem` يدويًا.
- أعمدة POS أصبحت schema عبر `TransactionColumn`.
- presets أصبحت من نفس preset engine المستخدم في الفواتير والمرتجعات.
- تفضيل preset أصبح محفوظًا عبر `POSPreferences` داخل `settings_service` وبنطاق user/branch/profile.
- density بقيت محفوظة بنفس النطاق وتطبّق على grid/input/buttons.

## أعمدة POS الجديدة

```text
#
Barcode
Item
Unit
Qty
Base Qty
Price
Total
Available
Barcode Scope
```

`Base Qty` و `Barcode Scope` مهمان لدعم باركود الوحدات:

- barcode_scope = item عند قراءة باركود المادة الأساسية.
- barcode_scope = unit عند قراءة باركود وحدة فرعية مثل كرتون/علبة.
- base_qty تعرض أثر معامل التحويل على المخزون.

## السلوك المقصود

إذا قرأ المستخدم باركود وحدة:

```text
ماء / كرتون / qty=1 / base_qty=24 / barcode_scope=unit
```

ولا يتم عرضه كمادة عادية بكمية قطعة واحدة.

## ما لم يتم تغييره عمدًا

- لم يتم تحويل POS بالكامل إلى `TransactionDocumentTab` لأن POS له workflow لمسي مختلف.
- لم يتم تغيير `pos_service.checkout()` لأنه أصبح في Phase 175 يحترم الباركود والوحدات والمخزون.
- لم يتم بناء Restaurant POS بعد. هذه المرحلة تمهّد له عبر `POSLineGrid` و`POSLineModel`.

## الفحوص

```text
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase176_pos_visual_grid_guard.py
```
