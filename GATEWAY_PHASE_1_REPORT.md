# Gateway Migration - Phase 1

## Objective
Start the phased migration toward a unified data-access contract:

```text
UI / PyQt -> Application Service -> Gateway Interface -> Remote API or Local Adapter
```

The first phase intentionally targets low-risk master data entities before invoices, inventory, accounting, or manufacturing.

## Implemented Scope

### Entities migrated
- Customers
- Suppliers

### New files
- `alrajhi_client/gateways/__init__.py`
- `alrajhi_client/gateways/entity_gateway.py`
- `alrajhi_client/gateways/local/__init__.py`
- `alrajhi_client/gateways/local/entity_gateway.py`
- `alrajhi_client/gateways/remote/__init__.py`
- `alrajhi_client/gateways/remote/entity_gateway.py`

### Modified files
- `alrajhi_client/core/services/entity_service.py`
- `alrajhi_client/core/services/catalog_service.py`

## What changed

### Before
`EntityService` and `CatalogService` imported legacy DAO objects directly:

```text
Service -> customer_dao / supplier_dao -> Repository -> DB/REST
```

### After
Services depend on a unified gateway contract:

```text
EntityService -> CustomerGateway / SupplierGateway
```

The factory `create_entity_gateways()` chooses the active adapter:

```text
Remote mode -> RemoteCustomerGateway / RemoteSupplierGateway -> RestClient
Local mode  -> LocalCustomerGateway / LocalSupplierGateway -> legacy DAO
```

## Important design decision
This phase does **not** remove SQLite and does **not** rewrite the DAOs. The legacy DAO remains only behind the local adapter. This reduces risk and allows a module-by-module migration.

## Validation performed
- Python syntax compilation passed for:
  - `alrajhi_client/gateways/*`
  - `alrajhi_client/core/services/entity_service.py`
  - `alrajhi_client/core/services/catalog_service.py`
- No remaining direct `customer_dao` or `supplier_dao` usage in:
  - `alrajhi_client/core/services`
  - `alrajhi_client/views`

## Remaining direct database access found
These are not part of Phase 1 and should be migrated later:

```text
views/main_window.py -> DatabaseConnection
views/dialogs/login_dialog.py -> DatabaseConnection
views/widgets/settings_widget.py -> DatabaseConnection
core/services/product_service.py -> item_dao/category_dao
core/services/invoice_service.py -> invoice_dao
core/services/voucher_service.py -> voucher_dao
core/services/warehouse_service.py -> warehouse_dao
core/services/branch_service.py -> branch_dao
core/services/cashbox_service.py -> cashbox_dao
core/services/inventory_service.py -> inventory_movement_dao
core/services/manufacturing_service.py -> manufacturing_dao
core/services/reporting_service.py -> ReportingDAO
```

## Recommended next phase
Migrate `Categories` and `Items` using the same pattern:

```text
ProductService -> ProductGateway / CategoryGateway -> Remote or Local adapter
```

Do **not** migrate invoices or inventory before catalog entities are stable.
