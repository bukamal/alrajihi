# Phase 330 — Purchase Apparel Inherited Cost Rate Fallback

## Problem
A live purchase-invoice path could still show inherited apparel variant costs as an exchange-rate-expanded value, for example `3,920,000,000,000 SYP` instead of `20,000 SYP`.

The previous fix handled the sales path and the normal purchase price key, but purchase invoice widgets can also pass the selected value through cost-oriented keys (`cost`, `cost_price`, `average_cost`, `unit_cost`). In some deployments storage and display currency settings are both SYP while legacy lookup data is still already multiplied by the exchange rate.

## Fix
- Treat purchase-like price keys as inherited purchase costs, not sale prices.
- Remove the early return when storage and display currency are equal for inherited apparel variant rows.
- Fall back to the current display-currency rate when `convert(1, storage, display)` returns `1`.
- Keep the correction narrow: only concrete apparel variants that inherit their cost from the base material are normalized.
- Do not change explicit variant prices, ordinary materials, sales pricing, printing, RBAC, network/API mode, or warehouse logic.

## Expected behavior
For a base apparel material with purchase cost `20,000 SYP`, selecting an inherited-cost variant in a purchase invoice must show:

- Cost: `20,000 SYP`
- Quantity `2`: total `40,000 SYP`

It must not show `280,000,000` or `3,920,000,000,000`.

## Validation
- Adds a release-gated regression test for purchase-like keys and the fallback exchange-rate path.
