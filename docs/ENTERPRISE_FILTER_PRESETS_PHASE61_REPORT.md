# Phase 61 — Enterprise Filter Presets

## الهدف
إكمال تجربة الجداول الاحترافية بعد Phase 60: لم تعد الجداول تدعم ترتيب وإخفاء الأعمدة فقط، بل أصبحت تدعم فلاتر أعمدة محفوظة وواجهات عرض Presets لكل جدول.

## المنجز
- إضافة `FilterBuilderDialog` داخل `SmartTableView`.
- دعم global local search + per-column contains filters عبر `SmartTableProxyModel`.
- إضافة حفظ واسترجاع filter state لكل جدول.
- إضافة View Presets تحفظ: حالة الأعمدة، الفلاتر، ووضع responsive columns.
- توسيع `TableToolbar` بزر Filters وقائمة Save View/View Presets.
- توسيع `TablePreferences` لحفظ قيم عامة وNamed Views.

## الضوابط
- لا SQL داخل الواجهة.
- لا كسر للطباعة الموحدة.
- لا استبدال Service/Gateway filtering؛ الفلترة الجديدة محلية واختيارية للشاشات المناسبة.
- منع إخفاء كل الأعمدة ما زال فعالًا من Phase 60.
