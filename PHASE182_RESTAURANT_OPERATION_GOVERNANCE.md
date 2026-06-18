# Phase 182 — Restaurant Operation Governance

This phase adds a restaurant-specific operation policy layer so Restaurant POS is
not controlled by direct UI button calls only. Sensitive operations now pass
through settings, RBAC permissions, and audit hooks.

## Added

- `core/services/restaurant_operation_policy.py`
- `settings_service.get_restaurant_settings()`
- Restaurant RBAC actions/permissions
- Restaurant operation guards in `RestaurantService`
- Restaurant operation visibility/enabled-state in `RestaurantPOSWidget`
- Client/server migration permissions for restaurant operations
- Arabic/German/English operation messages
- `tools/phase182_restaurant_operation_governance_guard.py`

## Governed operations

- Use Restaurant POS
- Open restaurant session
- Add order line / barcode entry
- Send order to kitchen
- Adjust bill
- Record payment
- Checkout table
- Update kitchen status

## Principle

Restaurant POS remains visually touch-first, but sensitive operations are now
controlled centrally. A service call should not bypass the same permissions and
settings applied by the UI.
