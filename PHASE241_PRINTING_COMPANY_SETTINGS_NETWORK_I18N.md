# Phase 241 — Printing Company Settings, Network Logo, and i18n Hardening

## Scope

First step in the browser-HTML printing unification work.  This phase focuses on
company identity, logo rendering, settings/API compatibility, multi-user network
mode, and Arabic/German/English print language selection.

## Changes

- `SettingsService.company_info()` now exposes a canonical printing contract:
  - `logo_path` for local workstation compatibility.
  - `logo_data_uri` for network/client-server portability.
  - `logo` as a backward-compatible alias.
  - language settings metadata.
- `SettingsService.save_company_info()` now writes through the settings gateway/API
  and stores both the local logo path and a Base64 data URI.
- Browser HTML templates now prefer `logo_data_uri` and inline local logos as data
  URIs, so all clients can print the same logo even if the original path exists
  only on one computer.
- Settings company tab now reads from `settings_service.company_info()` instead of
  local `config.get_company_info()`.
- Barcode labels now use the same company identity source, including
  `logo_data_uri`.
- Emergency template loader now records the real import failure and uses the print
  language/direction when fallback rendering is unavoidable.

## Network / multi-user note

A Windows path such as `C:\Users\admin\logo.png` is not valid for other client
machines.  Storing `company/logo_data_uri` in the settings table/API makes the
logo part of the shared configuration and therefore printable by every user and
client.

## Validation

- `python -m compileall -q alrajhi_client alrajhi_server tests`
- `python -m pytest -q tests/test_phase241_printing_company_settings_network_i18n.py`

