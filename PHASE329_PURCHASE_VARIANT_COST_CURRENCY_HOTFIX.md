# Phase 329 — Purchase Variant Cost Currency Hotfix

## Objective
Fix the remaining apparel pricing defect in purchase invoices where inherited variant purchase cost could be converted from storage currency to display currency more than once, producing values such as `3,920,000,000,000 ل.س` instead of `20,000 ل.س`.

## Scope
- Purchase invoice line selection for apparel variants.
- Manual variant lookup and barcode lookup paths.
- Inherited prices from the base material only.

## Changes
- Mark variant lookup rows when their purchase/sale price is inherited from the base material.
- Add a narrow transaction line model guard that collapses repeated display-currency conversion only for inherited apparel variant prices.
- Keep explicit variant prices untouched.
- Preserve the existing behavior for normal materials, sub-units, sales invoices, restaurant/cafe, API mode, RTL/LTR, and unified printing.

## Expected behavior
If the base apparel material has:
- Purchase price: `20,000 SYP`
- Sale price: `25,000 SYP`

Then selecting an inherited apparel variant in a purchase invoice must show:
- Cost: `20,000 ل.س`
- Total for quantity 2: `40,000 ل.س`

It must not show `280,000,000` or `3,920,000,000,000`.
