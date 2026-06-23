# -*- coding: utf-8 -*-
"""Branded workspace tab labeling policy for Phase 354.

The dashboard is fixed and not a tab.  Every real tab gets a visible type label
(main/sub) plus the business title so users can distinguish high-level pages
from nested document tabs at a glance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

try:  # Keep import safe for tests outside the PyQt runtime.
    from workspace.registry import PAGE_MANIFESTS
except Exception:  # pragma: no cover - fallback for static tooling
    PAGE_MANIFESTS: Mapping[str, object] = {}

BRANDED_TAB_PHASE = 354
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
    return "رئيسي" if kind == "main" else "فرعي"


def compose_tab_label(tab_id: str, title: str) -> BrandedTabLabel:
    clean_title = str(title or tab_id or "").replace("\n", " ").strip()
    kind = tab_kind_for_id(tab_id)
    label = label_for_kind(kind)
    # Keep the visible tab compact while still showing the requested main/sub label.
    display = f"{label} · {clean_title}" if clean_title else label
    tooltip = f"{label} — {clean_title}" if clean_title else label
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
