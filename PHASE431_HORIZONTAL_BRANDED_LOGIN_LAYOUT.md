# Phase 431 — Horizontal Branded Login Layout

## Goal

Replace the tall/narrow vertical LoginDialog with a wide horizontal branded surface aligned with the project visual identity.

The change is limited to the login presentation layer. It does not change authentication, remembered-user handling, language persistence, remote/local mode detection, activation, session creation, or password validation.

## Implemented changes

- Converted `LoginDialog` from a single vertical card into a horizontal split layout.
- Added a branded side panel using the existing first-run identity surface:
  - `firstRunBrandPanel`
  - project logo
  - application title
  - secure-login subtitle
  - mode/language chips
- Added a focused form panel using:
  - `firstRunFormPanel`
  - `firstRunFormTitle`
  - `firstRunFormSubtitle`
  - `loginCredentialsPanel`
  - `loginOptionsPanel`
  - `firstRunPrimary`
  - `firstRunSecondary`
- Added Phase 431 design tokens in `theme/brand.py`:
  - `login_horizontal_width`
  - `login_horizontal_height`
  - `login_horizontal_min_width`
  - `login_horizontal_min_height`
  - `login_horizontal_brand_width`
  - `login_horizontal_form_width`
- Added QSS support for:
  - `horizontal_branded_split`
  - `horizontal_brand_form_no_overlay`
  - `horizontal_compact`
- Preserved the Phase 368 password visibility rule: the eye button is a fixed-size layout peer, not an overlay inside the password field.
- Runtime language switching now refreshes the side brand panel text without rebuilding the dialog.
- RTL/LTR is respected by the dialog and panels.

## Explicit non-goals

- No authentication logic changes.
- No user/session/service changes.
- No activation workflow changes.
- No database or API changes.
- No POS/restaurant/payment/inventory changes.

## Validation

Added:

- `alrajhi_client/workspace/quality/horizontal_branded_login_contract.py`
- `tools/phase431_horizontal_branded_login_guard.py`
- `tests/test_phase431_horizontal_branded_login_layout.py`

Updated older login compatibility contracts/tests so that Phase 431 intentionally supersedes the older vertical-login restore assertions.

## Acceptance

The LoginDialog should now open as a wider, professional, horizontal split surface:

- brand identity side panel on one side;
- username/password/options/actions on the other side;
- no narrow/tall appearance;
- no password-eye overlap;
- no field/options overlap;
- language switching keeps text synchronized;
- visual identity is consistent with the current branded project surface.
