# Phase 31 — Restaurant Kitchen Stations

## Scope
Added kitchen-station routing for the restaurant vertical so Kitchen Display System tickets are no longer a single undifferentiated queue.

## Added
- `restaurant_kitchen_stations` table with default stations: Bar, Grill, Hot Kitchen, Dessert.
- `restaurant_menu_station_map` for assigning menu/items to a kitchen station.
- `station_id` on `kitchen_tickets`, `kitchen_ticket_lines`, and `restaurant_order_lines`.
- Station-aware `send_to_kitchen`: one KOT per station when a table order contains items routed to different stations.
- KDS station filter in the restaurant kitchen display widget.
- Local, remote, service, server route, and repository contracts.

## New endpoints
- `GET /api/restaurant/kitchen/stations`
- `POST /api/restaurant/kitchen/stations`
- `POST /api/restaurant/menu_items/<item_id>/station`
- `GET /api/restaurant/kitchen/tickets?station_id=<id>`

## Validation
- `architecture_guard`: passed.
- `pytest`: 33 passed, 1 existing non-fatal warning.
- `compileall`: passed.
