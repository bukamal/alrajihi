# Phase 312 — Cafe Analytics F-string Hotfix

## Scope

This phase fixes a CI-blocking syntax error in the cafe analytics status line inside the restaurant analytics widget.

## Changes

- Replaced nested translation calls inside an f-string with precomputed label variables.
- Preserved the cafe analytics status text semantics:
  - top modifier label
  - top modifier name fallback
  - low-stock alert count
- Added a regression test that parses the analytics widget with `ast.parse` and asserts the unsafe nested f-string pattern is not reintroduced.

## Governance

- No data access was added to client views.
- No currency formatting policy was changed.
- No restaurant/cafe service or gateway behavior was changed.
- The change is limited to a syntax-safe UI status text assembly.
