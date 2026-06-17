# Restaurant Delivery + Takeaway Phase 35

## Scope
Added a conservative delivery/takeaway workflow on top of the Phase 34 restaurant foundation.

## Added
- Takeaway orders without occupying a physical dining table.
- Delivery orders with customer name, phone, address, delivery fee, driver id, and delivery status.
- Delivery event ledger for status history.
- Server endpoints for creating/listing takeaway and delivery orders.
- Client service/gateway contracts for local and remote modes.

## Boundary
HTTP layers remain thin. Restaurant SQL remains inside the restaurant repository/local gateway boundary.

## Next
Advanced split bill and printer routing.
