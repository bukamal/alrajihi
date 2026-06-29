# Phase 443 — Lazy Page Factory Import Path Hotfix

## Problem

After Phase 436 introduced lazy loading, POS and restaurant pages were no
longer imported during `MainWindow` startup.  Windows runtime testing exposed a
packaging/runtime regression when the user opened those pages:

- `No module named 'views.widgets.pos_widget'`
- `No module named 'views.restaurant.restaurant_simple_pos_widget'`

The page itself was not necessarily broken.  The lazy loader was attempting to
resolve short module paths that are unsafe in packaged sessions.

## Fix

`PAGE_FACTORY_SPECS` in `alrajhi_client/views/main_window.py` now uses
fully-qualified package paths, for example:

- `alrajhi_client.views.widgets.pos_widget`
- `alrajhi_client.views.restaurant.restaurant_simple_pos_widget`
- `alrajhi_client.views.cafe`
- `alrajhi_client.views.apparel`

The lazy loader now includes a central resolver:

- `normalize_page_factory_module_name()`
- `page_factory_import_candidates()`
- `_is_missing_candidate_module()`

This preserves a source-tree fallback, but the source of truth is now packaged
runtime safe.

## Error message hardening

The error page now distinguishes a lazy import/module-path failure from a
REST/API failure.  If a `ModuleNotFoundError` occurs, the user sees a local
import/package diagnostic instead of a misleading server/REST message.

## Guarding

Added:

- `alrajhi_client/workspace/quality/lazy_page_factory_import_path_contract.py`
- `tools/phase443_lazy_page_factory_import_path_guard.py`
- `tests/test_phase443_lazy_page_factory_import_path.py`

The guard fails if any lazy factory path reverts to short forms such as
`views.widgets.pos_widget`.

## Scope

No POS, restaurant, inventory, payment, printing or visual business logic was
changed.  This is a lazy import-path hotfix only.
