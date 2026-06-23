# Phase 348 — Editable Entry & Return Unification

This phase unifies keyboard entry, text focus, and return document behavior.

## Scope

- Text inputs select their contents on focus and mouse click.
- Editable grids initially focus the material/item entry column.
- Enter opens the editor and clears placeholder/default values such as `0` while selecting real values.
- Sales and purchase return screens use the same editable transaction grid pattern as sales and purchase documents.
- Original invoice selection remains available as an assisted workflow, but it is no longer the primary entry dependency.
- Manual returns can be saved in local mode without selecting an original invoice; assisted returns still preserve original-invoice quantity validation.

## Guard

Run:

```bash
python tools/phase348_editable_entry_return_unification_guard.py
```

Outputs:

- `tools/audit_outputs/editable_entry_return_unification_matrix.csv`
- `tools/audit_outputs/editable_entry_return_unification_summary.json`
