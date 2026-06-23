# Phase 347 — Save Closes Workspace Tab

## الهدف
تغيير سياسة الحفظ حسب طلب المشغل: زر **حفظ** داخل أي تبويب رئيسي أو فرعي يحفظ المستند ثم يغلق التبويب بعد نجاح الحفظ، مع بقاء Dashboard سطحًا ثابتًا وليس تبويبًا.

## القاعدة الموحدة
- Dashboard لا تظهر كتبويب ولا تملك عنوان تبويب بصري.
- إغلاق آخر تبويب يعيد المستخدم إلى Dashboard الثابتة ولا يترك مساحة بيضاء.
- أمر الحفظ لا يستدعي `removeTab()` مباشرة.
- الإغلاق بعد الحفظ يتم فقط بعد إشارة `saved` الناجحة.
- الإغلاق يتم عبر `TabbedWorkspace.close_tab_at()` حتى تبقى سياسة اختيار التبويب المجاور والـ fallback موحدة.
- قبل الإغلاق يتم تعليم التبويب كـ clean حتى لا تظهر رسالة تجاهل تغييرات بعد حفظ ناجح.

## الملفات الأساسية
- `alrajhi_client/views/main_window.py`
  - أضيفت `_should_close_tab_after_save()`.
  - أضيفت `_close_saved_document_tab()`.
  - تم تعديل `_on_document_saved()` ليجدول إغلاق التبويب عبر `QTimer.singleShot(0, ...)` بعد اكتمال handlers الأخرى.
- `alrajhi_client/workspace/shell/save_close_after_save_contract.py`
- `tools/phase347_save_closes_tab_guard.py`
- `tests/test_phase347_save_closes_tab.py`

## سبب استخدام QTimer
إشارة `saved` قد تكون مربوطة أيضًا بتحديث القوائم أو إعادة تسمية التبويب. لذلك يتم تأجيل الإغلاق لدورة event loop التالية حتى تنفذ كل handlers الحالية أولًا، ثم يغلق التبويب بأمان.

## Opt-out
يمكن لأي تبويب خاص منع الإغلاق بعد الحفظ عند الحاجة بوضع:

```python
self.prevent_close_after_save = True
```

أو:

```python
self.stay_open_after_save = True
```

هذا لا يغيّر السياسة العامة، لكنه يحفظ مخرجًا آمنًا للشاشات التي تحتاج حفظًا متكررًا بدون إغلاق في المستقبل.

## التحقق
- `tools/phase347_save_closes_tab_guard.py`
- `tests/test_phase347_save_closes_tab.py`
- Release Gate محدث للمرحلة 347.
