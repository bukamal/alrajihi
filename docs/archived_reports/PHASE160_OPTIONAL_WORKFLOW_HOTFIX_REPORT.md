# Phase 160 - Optional Workflow Hotfix

## الهدف
جعل Workflow اختياريًا بدل أن يكون مسارًا إجباريًا لكل الفواتير.

## الإعدادات الجديدة
- `workflow/enabled`
  - `true`: تفعيل أزرار ومسار Workflow.
  - `false`: تعطيل Submit/Approve/Reject/Reopen وإبقاء Post فقط.

- `workflow/approval_required`
  - `true`: لا يسمح بالترحيل قبل الاعتماد.
  - `false`: يسمح بالترحيل بدون اعتماد، مع بقاء Workflow المبسط متاحًا.

## المنفذ فعليًا
- إضافة الإعدادات في migrations للعميل والخادم.
- إضافة checkbox في تبويب سير العمل داخل الإعدادات.
- تعديل `WorkflowPolicyService` لقراءة حالة التفعيل والاعتماد.
- تعديل `InvoiceService.post` للسماح بالترحيل المباشر عند تعطيل Workflow.
- تعديل أزرار الفواتير حسب الإعدادات:
  - Workflow OFF: يظهر Post فقط.
  - Workflow ON + Approval OFF: يظهر Submit/Post/Reopen.
  - Workflow ON + Approval ON: يظهر Submit/Approve/Reject/Post/Reopen.
- تعديل API الخادم ليتبع نفس السياسة.

## الاختبارات
- `python -m compileall -q alrajhi_client alrajhi_server tools` ✅
- `python tools/architecture_guard.py` ✅

## ملاحظة
القيمة الافتراضية بقيت `true/true` للحفاظ على سلوك النسخ السابقة. يمكن تعطيل Workflow من الإعدادات.
