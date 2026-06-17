# Phase 160 - Optional Workflow Deep Audit Fix

## Scope
Audited the optional workflow implementation and its integration points:
- settings defaults and persistence
- invoice UI workflow button visibility
- local invoice service transition rules
- server invoice workflow endpoint rules
- migrations for new/old databases
- architecture guard compatibility

## Findings
1. Optional workflow logic was present.
2. UI switches existed in Settings.
3. Invoice service supported these modes:
   - Workflow OFF: direct Post
   - Workflow ON + Approval OFF: Submit/Post
   - Workflow ON + Approval ON: Submit/Approve/Reject/Post
4. Server endpoint had corresponding checks.
5. Gap found: defaults were set to `true/true`, so fresh installations started with mandatory Workflow/Approval instead of optional/off.

## Fix
Changed defaults to optional/off:
- `workflow/enabled = false`
- `workflow/approval_required = false`

Applied consistently in:
- client migrations
- server migrations
- client WorkflowPolicyService fallback defaults
- server invoice API fallback defaults
- settings UI load defaults

## Validation
- `python tools/architecture_guard.py`: PASSED
- `python -m compileall -q alrajhi_client alrajhi_server tools`: PASSED
- Server fresh database settings check: PASSED
- Static rule audit for invoice service modes: PASSED

## Operational Result
Default behavior for a new single-admin/small-business install is fast mode:
- Save invoice
- Post directly

Advanced governance can be enabled from Settings:
- Enable Workflow
- Require Approval Before Posting

