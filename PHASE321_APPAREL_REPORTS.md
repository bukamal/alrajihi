# PHASE 321 — Apparel Reports

## Scope

Adds operational apparel reporting on top of the existing material variant engine. The feature remains inside the product/material gateway boundary and does not introduce a separate apparel DAO, repository, or gateway.

## Delivered

- Variant stock report by material, color, and size.
- Low-stock report using each variant reorder level.
- Aggregate report by parent material.
- Top color and top size sales aggregates.
- API/network mode endpoint for apparel reports.
- Client gateway and ProductService method for apparel reports.
- Apparel workspace report card with low-stock table and sales metrics.

## Design constraints

- Visible terminology uses translated `Variant code` / `رمز المتغير` / `Variantencode`; the technical storage field remains internal.
- The UI does not query SQLite directly.
- Remote/API mode uses `/api/items/variants/apparel-report`.
- RTL/LTR behavior follows the existing workspace direction helpers.
- Unified printing, currency formatting, and transaction behavior are not changed.

## Verification

- Static contract test: `tests/test_phase321_apparel_reports.py`.
- Release gate registration updated.
