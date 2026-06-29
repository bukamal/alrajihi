# Phase 435 — Login-to-MainWindow Transition Profiler & Overlay

This phase addresses the long silent delay after accepting LoginDialog and before MainWindow becomes visible.

## Scope

Phase 435 does not change authentication, activation, permissions, accounting, inventory, printing, or MainWindow behavior. It adds:

- A branded post-login transition overlay.
- A Qt-free startup timeline profiler.
- Runtime marks around login acceptance, MainWindow construction, and MainWindow show.
- Audit outputs for diagnosing slow startup segments.

## Added files

- `alrajhi_client/ui/post_login_transition_overlay.py`
- `alrajhi_client/workspace/runtime/startup_timeline_profiler.py`
- `alrajhi_client/workspace/quality/login_to_main_transition_contract.py`
- `tools/phase435_login_to_main_transition_guard.py`
- `tests/test_phase435_login_to_main_transition.py`

## Runtime outputs

When the application reaches the main window, the profiler writes:

- `tools/audit_outputs/startup_timeline.json`
- `tools/audit_outputs/startup_timeline.csv`

The most important field is:

- `post_login_to_main_ms`

This measures the delay between successful login and visible MainWindow.

## UX behavior

After login succeeds, the user sees a small branded overlay with status text:

- Loading user permissions.
- Building the main interface.
- Preparing the dashboard.
- Interface ready.

This prevents the transition from looking like an application freeze.

## Next step

If `post_login_to_main_ms` is high, Phase 436 should optimize startup by lazy-loading heavy modules instead of constructing every workspace before the main shell is visible.
