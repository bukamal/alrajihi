# Structure Remediation Phase 4

## Scope
This phase continues the structural cleanup from Phase 3 without changing UI behavior.

## Changes
- Removed direct `DatabaseConnection`/SQL usage from `alrajhi_client/core/services/advanced_approval_service.py`.
- Moved multi-level approval persistence into `LocalApprovalGateway`.
- Extended `ApprovalGateway` with advanced approval operations:
  - `ensure_advanced_schema`
  - `matrix_for`
  - `ensure_steps_for_request`
  - `pending_step`
  - `approve_current_step`
  - `request_status`
- Updated `architecture_guard.py` legacy allow-list.

## Result
- Legacy DatabaseConnection exceptions reduced from 6 to 5.
- Legacy SQL execution exceptions reduced from 6 to 5.

## Verification
- `python tools/architecture_guard.py` passes.
- `pytest -q` passes: 2 tests.
- `python -m compileall -q alrajhi_client alrajhi_server tools tests` passes.
