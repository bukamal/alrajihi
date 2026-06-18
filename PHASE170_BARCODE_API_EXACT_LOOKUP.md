# Phase 170 — Exact Barcode API Lookup

## Goal

Scanner input must resolve materials through exact barcode lookup in every runtime mode. A failed scan must never fall back to fuzzy material search or insert the first search result.

## Changes

- Added a read-only REST client method:
  - `RestClient.get_item_by_barcode(barcode)`
- Added an exact server API endpoint:
  - `GET /api/items/by-barcode?barcode=<code>`
  - `GET /api/items/by-barcode/<code>`
- Updated `RemoteItemGateway.get_by_barcode()` to use the exact endpoint instead of downloading the whole catalog.
- Kept a bounded old-server fallback: `GET /api/items?search=<code>&limit=10`, accepting only an exact `barcode == code` match.
- Added `DatabaseConnection.get_item_by_barcode()` for exact local lookup.
- Updated `ItemRepository.get_by_barcode()` and `ItemDAO.get_by_barcode()` to avoid full-catalog scans.

## Rules

- Barcode scan mode is exact only.
- No `LIKE`/fuzzy matching in the exact barcode API.
- No `self.list()` without filters in remote barcode lookup.
- No `records(self.get_items())` full-catalog scan in `ItemDAO.get_by_barcode()`.
- Not found returns `None` client-side and HTTP `404` server-side.

## Verification

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
```
