# Phase 191 — Manufacturing API / Unit Alignment

This phase aligns manufacturing data with the unified material/unit/barcode model.

## Implemented

- Added idempotent schema columns for BOM lines, BOM snapshots, reservations, consumptions, and outputs.
- Persisted `unit_id`, `conversion_factor`, base quantities, and barcode scope in local DAO flows.
- Mirrored the same fields in server manufacturing endpoints.
- Kept legacy operational quantities backward-compatible while adding explicit base quantity fields.
- Added guard `tools/phase191_manufacturing_api_unit_alignment_guard.py`.

## Rule

Manufacturing must not lose unit context. Component quantities can be entered in a selected unit, but stock and availability are always checked in base units.
