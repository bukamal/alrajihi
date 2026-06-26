# Phase 388 — Editable Grid Mouse Action Boundary

## الهدف
منع تعارض التنقل والتحرير داخل الجداول التحريرية مع أزرار الفأرة الجانبية مثل تعديل، حذف، طباعة، حفظ، أو أي زر خارج الجدول.

## المشكلة
كان إغلاق محرر الخلية بسبب فقدان التركيز عند الضغط على زر خارجي يُفسَّر كأنه Enter، فينتقل الجدول إلى الخلية التالية ويفتح محررًا جديدًا. النتيجة أن الزر الخارجي لا يستقبل النقرة بشكل موثوق.

## الإصلاح
- أصبح التنقل بعد إغلاق محرر الخلية مشروطًا بوجود نية صريحة من Enter/Shift+Enter.
- إغلاق المحرر بسبب mouse focus-out أو فتح dialog أو الضغط على زر جانبي لا ينقل التركيز داخل الجدول.
- بقيت إشارات EditNextItem/EditPreviousItem الخاصة بلوحة المفاتيح تعمل كالمعتاد.
- بعد كل إغلاق للمحرر يتم تصفير حالة التنقل المعلقة لمنع أي انتقال متأخر.

## الملفات
- `alrajhi_client/ui/table_keyboard_policy.py`
- `tools/phase388_editable_grid_mouse_action_boundary_guard.py`
- `tests/test_phase388_editable_grid_mouse_action_boundary.py`
- `alrajhi_client/workspace/quality/editable_grid_mouse_action_boundary_contract.py`
