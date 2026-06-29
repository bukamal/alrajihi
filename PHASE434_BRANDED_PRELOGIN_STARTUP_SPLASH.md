# Phase 434 — Branded Pre-login Startup Splash

This phase rebuilds the splash screen shown **before** LoginDialog. It does not add a post-login loader.

## Goals

- Remove the legacy yellow logo header visual.
- Remove unexplained white placeholder bars.
- Convert the old button-like labels into passive boot-stage indicators.
- Use the same calm blue/teal identity surface as the stabilized login screen.
- Keep the splash limited to pre-login startup feedback.

## Runtime behavior

The splash now shows:

1. Project identity panel.
2. Boot stages: database, license, login, shell.
3. One progress bar.
4. A clear current step label.
5. A detail line explaining what is being checked.

The long transition after login remains a separate concern and should be handled by a later login-to-main transition profiler/overlay phase.

## Files

- `alrajhi_client/views/splash_screen.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
- `alrajhi_client/workspace/quality/branded_prelogin_startup_splash_contract.py`
- `tools/phase434_branded_prelogin_startup_splash_guard.py`
- `tests/test_phase434_branded_prelogin_startup_splash.py`
