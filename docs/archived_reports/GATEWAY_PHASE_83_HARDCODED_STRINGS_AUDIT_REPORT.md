# GATEWAY PHASE 83 – Hardcoded Strings Audit & Cleanup Baseline

## الهدف
تنفيذ فحص شامل للنصوص المباشرة المتبقية بعد مراحل الترجمة 76-82، تمهيدًا لتحويلها تدريجيًا إلى نظام الترجمة المركزي بدون كسر منطق التشغيل.

## ما تم تنفيذه
- إضافة أداة فحص مستقلة:
  - `tools/verify_hardcoded_strings_audit.py`
- توليد ملف CSV تفصيلي:
  - `build/language_audit/hardcoded_arabic_literals.csv`
- توليد ملخص JSON:
  - `build/language_audit/hardcoded_arabic_summary.json`
- تصنيف النصوص حسب المسار:
  - واجهات مرشحة للترجمة.
  - قاعدة بيانات/مخططات/بيانات مرجعية.
  - API/Server.
  - أدوات داخلية.
  - ملفات أخرى.

## نتيجة الفحص
- إجمالي النصوص العربية المباشرة المرصودة: **1897**
- المرشحة مباشرة كواجهة مستخدم: **1192**
- API/Server: **211**
- قاعدة بيانات أو مخططات أو بيانات مرجعية: **211**
- أدوات داخلية: **33**
- أخرى: **250**

## أكثر الملفات احتواءً على نصوص مباشرة
1. `alrajhi_client/views/widgets/settings_widget.py` — 219
2. `alrajhi_client/views/widgets/reports_widget.py` — 215
3. `alrajhi_client/views/widgets/pos_widget.py` — 91
4. `alrajhi_server/api/manufacturing.py` — 89
5. `alrajhi_client/database/dao/manufacturing_dao.py` — 82
6. `alrajhi_client/views/widgets/dashboard_widget.py` — 67
7. `alrajhi_client/views/widgets/audit_log_widget.py` — 59
8. `alrajhi_client/views/widgets/branches_widget.py` — 48
9. `alrajhi_client/views/widgets/users_widget.py` — 44
10. `alrajhi_client/views/widgets/categories_widget.py` — 40

## ملاحظة مهمة
ليست كل النصوص المرصودة يجب تحويلها فورًا إلى ترجمة. بعضها:
- أسماء افتراضية داخل قاعدة البيانات.
- رسائل API داخلية.
- بيانات seed/migration.
- نصوص تقارير قد تكون مرتبطة بتخزين سابق.
- أدوات اختبار وحراسة.

لذلك تم اعتماد هذه المرحلة كتدقيق شامل وخريطة تحويل، وليس استبدالًا آليًا عدوانيًا.

## الاختبارات
- `python3 tools/verify_hardcoded_strings_audit.py` ✅
- `python3 -m compileall -q alrajhi_client alrajhi_server tools` ✅

## التوصية للمرحلة التالية
**Phase 84 – High-impact UI String Cleanup**

البدء بالملفات ذات الأثر الأعلى على المستخدم:
1. `settings_widget.py`
2. `reports_widget.py`
3. `pos_widget.py`
4. `dashboard_widget.py`
5. `audit_log_widget.py`
6. `branches_widget.py`
7. `users_widget.py`
8. `categories_widget.py`

التحويل يجب أن يكون يدويًا/انتقائيًا وليس Regex عامًا، حتى لا يتكرر كسر `QDialogButtonBox` أو إدخال أخطاء في منطق Qt.
