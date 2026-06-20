# PHASE259 Settings Contract Coverage Audit

## Objective

Unify settings coverage for every registered shell family without importing PyQt at audit time:

- Document Shells
- Transaction Shells
- List Workspaces
- Report Shells
- Operational Shells such as POS and Restaurant

The purpose of this phase is not to redesign all settings screens visually. The purpose is to make settings coverage explicit, inspectable, network-aware, profile-aware, and testable.

## Added

### `alrajhi_client/workspace/settings/settings_contract.py`

Introduces:

- `SettingsKeyDescriptor`
- `SettingsScopeDescriptor`
- `settings_descriptor_for(scope)`
- `settings_scope_descriptors()`
- `collect_shell_settings_scopes()`
- `uncovered_settings_scopes()`
- `settings_coverage_matrix()`
- `validate_settings_scope_descriptors()`

Each settings scope declares:

- UI section key
- Settings service getter
- API resource
- network mode
- language keys
- currency keys
- print keys
- operation setting prefixes
- required setting keys
- profile awareness

### `tools/settings_contract_coverage_audit.py`

Creates:

`tools/audit_outputs/settings_contract_coverage_matrix.csv`

The audit fails if any shell/list/report/operational settings scope is not covered by a settings contract.

### Settings UI coverage

Expanded `features/settings/settings_document_tabs.py` with additional settings sections:

- transactions
- materials
- categories
- parties
- finance
- branches
- manufacturing
- reports
- pos
- users

The existing sections remain:

- company
- accounting
- inventory
- restaurant
- printing
- ui
- security

### `SettingsService.settings_contract_coverage()`

Read-only helper that returns the settings matrix, uncovered scopes, available sections, and settings API resource.

## Network/API rule

All settings declared in the contract are routed through `SettingsService`, which uses `SettingsGateway`. Therefore the same contract works in local mode and remote client/server mode through:

`/api/settings/<path:key>`

## Language rule

The settings contract explicitly tracks:

- `language`
- `language/print`
- `language/report`

This keeps UI language, print language, and report language separate for Arabic, English, and German.

## Currency rule

The settings contract tracks:

- `base_currency`
- `display_currency`
- `currency_decimals`
- `number_format`

This complements `MoneyDisplayPolicy`; the settings contract declares the source keys, while `MoneyDisplayPolicy` formats values.

## Test result

- `python -m compileall -q alrajhi_client alrajhi_server tests tools`: passed
- `python tools/settings_contract_coverage_audit.py`: passed
- `pytest -q`: `193 passed, 1 warning`

The remaining warning is the existing `PytestCollectionWarning` for `TestReportingDAO` with `__init__`, not a regression in this phase.
