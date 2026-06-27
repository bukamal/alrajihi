# -*- coding: utf-8 -*-
"""Phase398 contract: category inline creation must expose a visible Save action.

The category editor is a card-form document.  Inline layout policy hides duplicate
header cards, so the editor must not depend on a header-only Save button when it
is embedded in the Categories master-detail workspace.
"""
from __future__ import annotations

CATEGORY_INLINE_SAVE_CONTRACT = {
    "phase": 398,
    "editor": "alrajhi_client/features/categories/category_editor_tab.py",
    "required_surfaces": [
        "CategoryHeaderPanel",
        "CategoryInlineActionBar",
        "inline_save_btn",
        "workspace_save",
    ],
    "invariants": [
        "standalone_header_save_kept",
        "inline_save_outside_hidden_document_header",
        "inline_save_uses_same_workspace_save_command",
        "permission_state_applies_to_inline_save",
    ],
}

__all__ = ["CATEGORY_INLINE_SAVE_CONTRACT"]
