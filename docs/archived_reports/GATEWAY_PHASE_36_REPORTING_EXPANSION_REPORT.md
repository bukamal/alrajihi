# Phase 36 - Reporting Expansion

## الهدف
توسيع تبويب التقارير ليغطي تقارير العملاء والموردين وحركاتهم، وربط التقارير المتقدمة التي أضيفت في مراحل Ledger/Monitoring داخل نفس تبويب التقارير.

## ما تم تطبيقه

### 1. توسعة ReportingGateway
أضيفت عقود جديدة:

- customer_statement(customer_id, start_date, end_date)
- supplier_statement(supplier_id, start_date, end_date)
- customer_balances()
- supplier_balances()
- customer_aging(as_of_date)
- supplier_aging(as_of_date)
- trial_balance()

مع تطبيقها في:

- gateways/local/reporting_gateway.py
- gateways/remote/reporting_gateway.py
- core/services/reporting_service.py

### 2. Remote API reports
أضيفت endpoints جديدة:

- GET /api/reports/customers/<id>/statement
- GET /api/reports/suppliers/<id>/statement
- GET /api/reports/customers/balances
- GET /api/reports/suppliers/balances
- GET /api/reports/customers/aging
- GET /api/reports/suppliers/aging
- GET /api/reports/trial_balance

### 3. RestClient
أضيفت methods مقابلة في:

- database/connection_rest.py

### 4. Local ReportingDAO
تم تحسين حركات العملاء والموردين لتشمل:

#### العميل
- فواتير البيع = مدين
- مرتجعات البيع = دائن
- سندات القبض = دائن

#### المورد
- فواتير الشراء = دائن
- مرتجعات الشراء = مدين
- سندات الدفع = مدين

كما أضيفت أرصدة العملاء/الموردين وأعمار الديون/الدائنين وميزان المراجعة.

### 5. ReportsWidget
أضيفت تبويبات جديدة:

- ميزان المراجعة
- كشف حساب عميل
- كشف حساب مورد
- أرصدة العملاء
- أرصدة الموردين
- أعمار ديون العملاء
- أعمار ديون الموردين
- مطابقة Ledger
- Dual Read
- جاهزية Ledger
- Offline Queue
- فحص الوحدات

مع فلاتر جديدة:

- العميل
- المورد

## الفحوصات

- compileall: PASS
- architecture_guard: PASS
- ReportingGateway method check: PASS
- AST syntax check: PASS
- zip test: PASS

## ملاحظات

- تبويبات Ledger و Offline Queue قراءة فقط.
- تقرير فحص الوحدات يعرض حالة تشغيلية مختصرة؛ التقرير التفصيلي لا يزال محفوظاً في UNIT_CONVERSION_ADVANCED_TEST_REPORT.md.
- تقارير أعمار الديون تعتمد على آخر حركة وتوزّع الرصيد الحالي على bucket واحد، وليست ageing تفصيلياً لكل فاتورة مستحقة بعد. هذا مناسب كمرحلة تشغيلية أولى، ويمكن تطويره لاحقاً إلى ageing invoice-level.
