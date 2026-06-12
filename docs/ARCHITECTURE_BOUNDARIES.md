# Architecture Boundaries

## Phase 11 rule

The desktop UI must not talk to DAO objects directly.

Allowed flow:

```text
views / widgets
→ core/services
→ gateways
→ remote REST adapter or local DAO adapter
```

Forbidden flow:

```text
views / widgets
→ database.dao
```

Also forbidden as a new dependency without explicit review:

```text
views / widgets / core/services
→ database.connection.DatabaseConnection
```

## Why

Gateway migration phases 1-10 moved the main business modules behind a single access contract. This file fixes that boundary as a project rule so future work does not reintroduce direct DAO coupling.

## Enforcement

Run:

```bash
python tools/architecture_guard.py
```

The guard fails when `alrajhi_client/views` or `alrajhi_client/core/services` imports `database.dao.*` directly.

Direct `DatabaseConnection` usage is still present in a small legacy allow-list for login, settings, offline queue, audit/backup, and return services. These are tracked technical debt, not a preferred pattern.

## Next migration targets

1. Move `sales_return_service.py` behind `SalesReturnGateway`.
2. Move `purchase_return_service.py` behind `PurchaseReturnGateway`.
3. Isolate settings/offline-queue access behind admin/system services.
4. Remove the `DatabaseConnection` legacy allow-list after those migrations.
