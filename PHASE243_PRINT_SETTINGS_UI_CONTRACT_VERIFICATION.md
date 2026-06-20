# PHASE 243 — Print Settings UI Contract Verification

## Scope
Verified that the print settings tab already exists, then extended it without duplicating it.

## Changes
- Added missing company identity toggles to the unified print settings contract: company name, address, phone, email, tax number, commercial register and website.
- Added print-language selection directly in the print settings tab while preserving the dedicated language tab.
- Added reverse-table-column setting for RTL browser HTML edge cases.
- Added a test-print action that uses `PrintingService` and therefore the same browser HTML / SettingsGateway / multi-user contract as real documents.
- Updated `print_templates.py` so every company identity line is governed by settings.
- Updated the lightweight workspace `PrintingSettingsTab` to expose the same core settings contract.

## Network / multi-user note
All values are persisted through `SettingsService.set()` and therefore through `SettingsGateway`; in client mode this goes through the server settings API. No new local-only `QSettings` storage was introduced.

## Language note
The print tab now writes `language/print` using `settings_service.save_language_settings(...)`, preserving UI and report language settings.
