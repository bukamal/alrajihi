# -*- coding: utf-8 -*-
"""Workspace tab labeling policy.

The dashboard is fixed and not a tab.  Real tabs keep their internal kind
(main/sub) for lifecycle metadata, but the visible text is now the business title
only.  Phase373 removes the visible Arabic main/sub prefixes from tab captions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

try:  # Keep import safe for tests outside the PyQt runtime.
    from workspace.registry import PAGE_MANIFESTS
except Exception:  # pragma: no cover - fallback for static tooling
    PAGE_MANIFESTS: Mapping[str, object] = {}

BRANDED_TAB_PHASE = 373
FIXED_DASHBOARD_TAB_ID = "dashboard"
DOCUMENT_TAB_PREFIXES = (
    "invoice:",
    "return:",
    "item:",
    "category:",
    "customer:",
    "supplier:",
    "voucher:",
    "expense:",
    "bom:",
    "production_order:",
    "branch:",
    "warehouse:",
    "cashbox:",
    "bank_account:",
    "warehouse_transfer:",
    "user:",
    "settings:",
)


@dataclass(frozen=True)
class BrandedTabLabel:
    tab_id: str
    title: str
    kind: str
    label: str
    display_text: str
    tooltip: str


def tab_kind_for_id(tab_id: str) -> str:
    tab_id = str(tab_id or "")
    if tab_id in PAGE_MANIFESTS and tab_id != FIXED_DASHBOARD_TAB_ID:
        return "main"
    if tab_id.startswith(DOCUMENT_TAB_PREFIXES):
        return "sub"
    return "sub" if ":" in tab_id else "main"


def label_for_kind(kind: str) -> str:
    """Return the internal non-visible tab kind label.

This value is stored in tab metadata only.  It is intentionally not rendered in
``display_text`` so workspace tabs show clean business titles without the old
main/sub prefixes.
    """
    return "main" if kind == "main" else "sub"


def compose_tab_label(tab_id: str, title: str) -> BrandedTabLabel:
    clean_title = str(title or tab_id or "").replace("\n", " ").strip()
    kind = tab_kind_for_id(tab_id)
    label = label_for_kind(kind)
    # Phase373: visible tab captions must be the business title only.  The kind
    # is still available through ``kind``/``label`` metadata for lifecycle logic.
    display = clean_title or str(tab_id or "")
    tooltip = clean_title or str(tab_id or "")
    return BrandedTabLabel(tab_id=str(tab_id or ""), title=clean_title, kind=kind, label=label, display_text=display, tooltip=tooltip)


__all__ = [
    "BRANDED_TAB_PHASE",
    "FIXED_DASHBOARD_TAB_ID",
    "DOCUMENT_TAB_PREFIXES",
    "BrandedTabLabel",
    "tab_kind_for_id",
    "label_for_kind",
    "compose_tab_label",
]
