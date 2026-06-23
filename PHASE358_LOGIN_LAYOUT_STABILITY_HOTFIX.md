# Phase 358 — Login Layout Stability Hotfix

## الهدف
إعادة تنسيق شاشة تسجيل الدخول بعد أن تسبب التصميم المقسوم العريض في تداخل العناصر وتشوه التخطيط، خصوصًا مع النصوص الطويلة والترجمات الألمانية/العربية وزر تبديل الحساب.

## التغييرات
- تحويل شاشة تسجيل الدخول إلى تخطيط رأسي مركزي ثابت بدل لوحة جانبية عريضة.
- إضافة `login_brand_header` كعنوان هوية مدمج أعلى النموذج.
- حصر عرض نموذج الدخول عبر `login_form_max_width`.
- تحويل خيارات المستخدم واللغة إلى لوحة `loginOptionsPanel` داخل `QGridLayout` لتجنب التداخل.
- تقصير نص زر تبديل الحساب مع إبقاء النص الكامل كـ tooltip.
- إضافة QSS خاص بـ `firstRunLoginHeader` وحقول الدخول وخيارات الدخول.
- رفع `brand_phase` إلى 358.

## التحقق
- `tools/phase358_login_layout_stability_guard.py`
- `tests/test_phase358_login_layout_stability.py`
