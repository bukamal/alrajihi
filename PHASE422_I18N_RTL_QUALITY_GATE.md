# Phase 422 — i18n / RTL Quality Gate

## Purpose

Phase 422 adds a project-wide quality gate for language and direction behavior.
The goal is not to add another UI feature.  The goal is to prevent regressions in
Arabic RTL, German/English/French LTR, printing language labels, transaction
column labels, restaurant/POS terminology, and runtime language switching.

## What changed

Added a Qt-free contract:

- `alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py`

Added a static audit module:

- `alrajhi_client/workspace/quality/i18n_rtl_quality_audit.py`

Added a release guard:

- `tools/phase422_i18n_rtl_quality_guard.py`

Added tests:

- `tests/test_phase422_i18n_rtl_quality.py`

Added release outputs:

- `tools/audit_outputs/i18n_rtl_quality_matrix.csv`
- `tools/audit_outputs/i18n_rtl_quality_coverage.json`
- `tools/audit_outputs/i18n_rtl_translation_key_usage.json`

## Enforced invariants

- Supported languages remain exactly: Arabic, German, English, French.
- Arabic remains the only RTL language.
- German, English and French remain LTR.
- Critical shell, transaction, POS/restaurant/cafe, settings, printing and report keys are translated in every supported language.
- Format placeholders such as `{module}` and `{error}` stay aligned between Arabic and translated strings.
- Runtime language switching continues to propagate table direction through `apply_table_direction_tree()`.
- MainWindow applies the active language direction to the clean menu bar.
- Phase416 remains the runtime screenshot/QTest harness for real Qt evidence.

## Intentional non-goals

- The monolithic `translator.py` is not split in this phase.
- Legacy screens with explicit `setLayoutDirection()` are audited, not deleted.
- Real visual screenshots still require running the Phase416 runtime harness on a machine with PyQt5.

## Recommended manual runtime check

After installing this phase, run:

```bash
python tools/run_phase416_runtime_acceptance.py --output-dir tools/audit_outputs/runtime_acceptance
```

Then compare the Arabic RTL and German LTR screenshots:

- `tools/audit_outputs/runtime_acceptance/shell_snapshot_ar.png`
- `tools/audit_outputs/runtime_acceptance/shell_snapshot_de.png`

The expected result is that the clean shell owns the top bar in both directions,
with no old topbar artifact in the left upper corner.
