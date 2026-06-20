# Phase 273 — Settings Navigation / Diagnostics Alignment

## Scope

This phase verifies that the Settings workspace already contains a diagnostics tab and fixes the settings navigation/title mismatch that could occur after changing the UI language.

## Findings

The diagnostics view already existed in `SettingsWidget.create_diagnostics_tab()`.  The problem was not absence of diagnostics.  The problem was that the settings page had two separate tab lists:

- the construction list in `SettingsWidget.__init__`
- the language-refresh label list in `_refresh_language_texts()`

The refresh list was stale and shorter than the real tab list.  It missed tabs such as settings profiles, unified contracts, workflow, and others.  After a language change, labels could shift and no longer match their tab content.

## Changes

- Added a canonical `_settings_tab_specs()` registry.
- The same registry now builds tabs and refreshes tab labels.
- Enabled scroll buttons and text eliding for the large settings tab set.
- Kept diagnostics inside Settings instead of adding a new top-level page.
- Expanded diagnostics to include contract-health summaries for:
  - Document Shell
  - List Workspace
  - Report Shell
  - Operational Shell
  - Settings Contract
  - RBAC Contract
  - Branch Scope
  - Offline Sync
  - End-to-End Scenarios
  - Runtime Smoke Hooks
- Added Arabic, English, and German translations for the expanded diagnostics title/help.

## Guarantees

- Tab title/content mapping no longer depends on two different lists.
- Diagnostics remains in Settings.
- No extra top-level settings tab was introduced.
- The fix is safe for network/server-client mode because it does not introduce local-only settings storage.
