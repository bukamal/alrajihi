# PHASE276_REPORT_PRINTING_UNIFICATION_CONFIRMATION

Confirms and hardens ReportsWidget printing.

- The visible report print button uses `ReportsPhase36Mixin.print_report()` -> `printing_service.report_print()` -> browser HTML.
- `report_print`, `report_preview`, and `report_pdf` all route through the unified browser HTML renderer.
- Report printing is controlled by `reports/operations/allow_print` through `report_operation_policy.OP_PRINT`.
- The setting is now visible in the main settings contracts screen, not only in the lightweight settings document tab.
- Report print template remains `printing/report_template` and is read via `SettingsService.get_report_settings()`.
- Report HTML uses `print_templates.report_html()`, company header, logo settings, print language, and browser-based output.
