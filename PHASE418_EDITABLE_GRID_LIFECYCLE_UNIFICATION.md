# Phase 418 — Editable Grid Lifecycle Unification

## الهدف

هذه المرحلة تنقل قاعدة دورة حياة الصفوف من فاتورة البيع فقط إلى الجداول التحريرية التشغيلية الأخرى التي تستخدم نفس نمط إدخال السطور.

المبدأ الحاكم:

- `Enter` للتأكيد والتنقل فقط.
- إنشاء صف جديد يتم عبر بوابة واحدة idempotent.
- لا يسمح بوجود أكثر من صف فارغ واحد في نهاية الجدول.
- زر `Insert` أو `Add Line` يعيد استخدام الصف الفارغ الأخير إن كان موجودًا.
- الجداول القديمة المعزولة في Phase 417 لا تُعاد إلى مسار الإنتاج.

## النطاق

تم توحيد دورة حياة الصفوف في:

- فواتير البيع والشراء والمرتجعات عبر `TransactionLineModel` من Phase 415.
- تحويلات المستودع عبر `InventoryTransferLinesModel`.
- BOM / مكونات التصنيع عبر `BomComponentsModel`.
- جداول وحدات المادة تبقى يدوية: لا إنشاء صف تلقائي عند Enter، والإضافة تتم فقط بزر إضافة وحدة أو تحميل بيانات المادة.

## التعديلات الأساسية

### InventoryTransferLinesModel

أضيفت الدوال التالية:

- `is_empty_line()`
- `trim_extra_trailing_empty_lines()`
- `ensure_single_trailing_empty_line()`

وأصبح:

- `add_empty_line()` يستدعي `ensure_single_trailing_empty_line()`.
- `add_item_from_lookup()` يستخدم الصف الفارغ الموجود بدل إنشاء صف إضافي.
- الصف الفارغ الافتراضي يبدأ بكمية `0` حتى يمكن اعتباره صفًا فارغًا حقيقيًا.

### BomComponentsModel

أضيفت الدوال التالية:

- `is_empty_line()`
- `trim_extra_trailing_empty_lines()`
- `ensure_single_trailing_empty_line()`

وأصبح:

- `add_empty_line()` idempotent.
- `add_item()` يستخدم الصف الفارغ الموجود بدل إنشاء صف جديد عند وجود trailing blank.

### Unified Grid Navigation Policy

تم توسيع المسارات Qt-free لتشمل:

- `inventory_transfer`
- `warehouse_transfer`
- `bom`
- `bom_components`
- `material_units`

المسارات المعتمدة:

- التحويلات: `item -> unit -> qty -> notes`
- BOM: `item -> unit -> qty -> waste_percent -> unit_cost -> total -> notes`
- وحدات المادة: `unit_name -> conversion_factor -> barcode -> price`

## النتيجة

أصبح محرك Enter في `StandardTableKeyboardMixin` قادرًا على الاعتماد على نفس بوابة الصف الواحد في الفواتير، التحويلات، والتصنيع. هذا يقلل خطر تكرار الصفوف عند نهاية السطر بسبب تداخل `Enter + closeEditor + dataChanged + AddLine`.

## حدود المرحلة

لم يتم تشغيل QTest Runtime فعلي هنا لأن PyQt5 غير مثبت في هذه البيئة. تم تثبيت العقود والاختبارات Qt-free/static. الاختبار الحاسم يبقى عبر Phase 416 Runtime Acceptance Harness على جهاز التشغيل.
