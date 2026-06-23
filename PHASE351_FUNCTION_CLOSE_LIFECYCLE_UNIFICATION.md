# PHASE 351 — Function Close Lifecycle Unification

## Goal
Unify the internal Close button behavior across all document-like workspace functions, not only invoice and return creation tabs.

## Policy
Any internal Close/Cancel button that semantically closes a workspace business page must delegate to the owning tab lifecycle used by the tab-bar X button. This guarantees:

- one unsaved-change confirmation path;
- complete tab closure instead of hiding only the inner widget;
- safe previous/next tab selection;
- fixed Dashboard fallback when the last tab closes;
- no white blank workspace surface after closing.

## Covered function families

- transactions and returns;
- materials;
- inventory and warehouse documents;
- finance documents;
- branch documents;
- user documents;
- manufacturing BOM, production order and lifecycle documents;
- hosted legacy dialog documents.

## Runtime files

- `alrajhi_client/workspace/shell/functional_close_policy.py`
- `alrajhi_client/workspace/documents/base_document_tab.py`
- `alrajhi_client/features/dialog_documents/dialog_document_tab.py`
- document tabs under materials, inventory, finance, branches, users and manufacturing.

## Guard

- `tools/phase351_function_close_lifecycle_guard.py`
- `tests/test_phase351_function_close_lifecycle.py`
