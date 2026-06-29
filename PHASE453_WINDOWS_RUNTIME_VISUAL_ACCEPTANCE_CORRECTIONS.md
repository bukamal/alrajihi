# Phase 453 — Windows Runtime Visual Acceptance Corrections

Phase 453 is driven by actual Windows screenshots after Phase 452. The goal is not a new feature; it is a runtime-facing visual acceptance layer that prevents native Windows/Fusion Qt controls, late-created lazy widgets, local invoice styles, POS metric styles, and English runtime labels from breaking the central identity.

## Scope

- Enforce Fusion style at startup through `install_windows_runtime_visual_acceptance(app)` before central theme application.
- Add a final `apply_windows_runtime_visual_acceptance(...)` pass after lazy workspace visual polish.
- Add central QSS selectors for Windows runtime controls, tables, headers, combo/dropdown/spin buttons, Login, POS metrics, POS scan input, payment shell, and material editor cards.
- Suppress legacy invoice local QSS and route invoice visuals through `apply_document_layout_policy`.
- Remove local POS metric `setStyleSheet` usage and convert it to central semantic properties.
- Add Arabic label cleanup for screenshot-visible labels such as `row density`, `Filters`, `Fit`, and `Restaurant table Takeaway / session`.
- Strengthen document-editor role mapping for `HeaderCard`, `ActionCard`, `RightPanel`, `TotalsCard`, and `BottomActionBar`.

## Non-scope

No change to invoice calculations, POS checkout, inventory, DAO/API, printing, permissions, activation, routing, Enter traversal, or persistence.

## Verification

Use:

```bash
python3 tools/phase453_windows_runtime_visual_acceptance_guard.py
python3 -m pytest tests/test_phase453_windows_runtime_visual_acceptance_corrections.py
```
