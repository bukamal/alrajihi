# Phase 207 — Party Governance / Workspace Hardening

This phase brings customers and suppliers under the same governance pattern used for materials, finance, inventory, and manufacturing.

Implemented:
- Added `party_operation_policy` for customer/supplier view/create/edit/delete operations.
- Added `settings_service.get_party_settings()`.
- Added party/customer/supplier permission actions and RBAC mappings.
- Routed `EntityService` through the policy layer so UI bypasses do not skip permissions/settings.
- Hardened `PartyEditorTab` into read-only mode when create/edit is not allowed.
- Hardened Customers/Suppliers workspaces to use document tabs first, source-row-safe selection, and no `AddEntityDialog` fallback in the normal path.
- Dashboard quick actions prefer `open_party_document()`.

Legacy add/edit dialogs are no longer part of the normal customer/supplier workspace flow.
