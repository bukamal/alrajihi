# GATEWAY PHASE 72 – Dashboard Design System Safe Refresh

## الهدف
تحديث لوحة التحكم بصريًا بما يتوافق مع الهوية البصرية المركزية للراجحي، مع الالتزام بقاعدة الاستقرار بعد Phase 65/71.

## نطاق التعديل
تم تعديل لوحة التحكم فقط:

- `alrajhi_client/views/widgets/dashboard_widget.py`
- إضافة أداة تحقق:
  - `tools/verify_dashboard_design_system.py`

## ما تم تنفيذه

1. ربط لوحة التحكم بمصدر الهوية المركزي:
   - `ThemeManager`
   - `theme.brand.BRAND`

2. إضافة دوال آمنة داخل لوحة التحكم:
   - `_dc(key, fallback)` لجلب ألوان الثيم مع fallback.
   - `_dashboard_product_name()` لجلب اسم بطاقة المطور من الهوية المركزية.

3. تحديث مناطق لوحة التحكم الرئيسية:
   - خلفية لوحة التحكم من `bg_window`.
   - تدرج الـ Hero من ألوان الراجحي: `primary`, `primary_2`, `accent`.
   - ألوان البطاقات من `card_bg`, `border`, `text_primary`, `text_secondary`.
   - بطاقة المطور تستخدم اسم المنتج من `BRAND['developer_card_name_ar']`.

4. تحسين النص التسويقي في Hero:
   - العنوان: `لوحة تحكم الراجحي`
   - الوصف: `نظرة تشغيلية موحدة للمحاسبة، المستودعات، التصنيع، والتنبيهات`

## ما لم يتم تغييره عمدًا

لم تتم إضافة أي طبقات Runtime خطرة:

- لا يوجد `EventFilter` عام.
- لا يوجد `widget_polish.py`.
- لا يوجد تعديل QtWebEngine.
- لا يوجد `--shm-helper` أو Chromium flags.
- لم يتم تعديل جميع النوافذ أو الجداول دفعة واحدة.

## الاختبارات

تم تنفيذ:

- `python3 tools/verify_dashboard_design_system.py`
- `python3 tools/verify_requirements_file.py`
- `python3 -m compileall -q alrajhi_client tools`

النتيجة: ناجحة.

## التوصية

اختبر تشغيل البرنامج من Linux أولًا:

```bash
python3 alrajhi_client/main.py
```

ثم راقب لوحة التحكم فقط. إذا استقرت، ننتقل في Phase 73 إلى شريط التنقل أو شاشة تسجيل الدخول، وليس إلى كل الجداول دفعة واحدة.
