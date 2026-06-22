# Phase 315 — Product Variants Foundation

## الهدف

تأسيس دعم متغيرات المواد للألبسة بدون كسر المواد العادية أو الوحدات الفرعية.

## القاعدة

- الوحدات الفرعية تبقى للتعبئة والتحويل الكمي مثل قطعة/كرتونة/كغ/غرام.
- المتغيرات `item_variants` تمثل نسخة مخزنية من المادة مثل اللون والمقاس.
- المادة الأصلية تبقى هي الجذر المحاسبي والكتالوجي.

## ما أضيف

- جدول `item_variants` في العميل والخادم.
- حقول: `item_id`, `color`, `size`, `sku`, `barcode`, `sale_price`, `cost_price`, `quantity`, `reorder_level`, `is_active`.
- منع تكرار نفس اللون/المقاس لنفس المادة.
- منع تكرار الباركود بين المادة، وحداتها، ومتغيراتها.
- واجهات Service/Gateway/DAO للعميل.
- REST API للخادم:
  - `GET /api/items/<id>/variants`
  - `POST /api/items/<id>/variants`
  - `PUT /api/items/variants/<variant_id>`
  - `DELETE /api/items/variants/<variant_id>`
  - `GET /api/items/variants/by-barcode`
- lookup الباركود يمكنه الآن إرجاع `barcode_scope = variant` مع `matched_variant`.

## ما لم يتغير

- المواد العادية لا تُجبر على استخدام المتغيرات.
- الوحدات الفرعية الحالية لم تتغير.
- المطعم والكافي والطباعة والعملة لا تعتمد على منطق جديد.
- لا يوجد محرك ألبسة مستقل بعد؛ هذه مرحلة الأساس فقط.
