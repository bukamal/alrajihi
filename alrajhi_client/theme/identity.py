# -*- coding: utf-8 -*-
"""Phase 352: brand identity contract for Al Rajhi UI surfaces.

This module is intentionally PyQt-free.  It defines the visual identity
expected by startup, login, activation, shell, tabs, actions, tables, dialogs
and transaction surfaces.  Runtime widgets should consume the tokens exposed
from :mod:`theme.brand` and avoid local literal colors.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

IDENTITY_PHASE = 352
IDENTITY_SOURCE_LOGO = "alrajhi_client/assets/brand/logo.png"


@dataclass(frozen=True)
class BrandColorSpec:
    key: str
    light: str
    dark: str
    role: str
    description: str


@dataclass(frozen=True)
class BrandSurfaceSpec:
    key: str
    token_keys: Sequence[str]
    description: str


# Palette is derived from the bundled logo family: deep ink/navy, blue-teal,
# controlled gold/sand accent, and soft financial surfaces.
BRAND_COLORS: Sequence[BrandColorSpec] = (
    BrandColorSpec("brand_ink", "#071A2E", "#EAF6FF", "identity", "Deep logo ink for high contrast text and shell chrome."),
    BrandColorSpec("brand_navy", "#083A63", "#102C44", "identity", "Stable accounting/navy anchor used by menus and tab chrome."),
    BrandColorSpec("brand_blue", "#0A6D9A", "#4FB3E8", "identity", "Dominant blue extracted from the project logo."),
    BrandColorSpec("brand_teal", "#087D78", "#41C7BD", "identity", "Logo teal used for active accents and progression."),
    BrandColorSpec("brand_gold", "#C99A2E", "#F0C15A", "identity", "Restrained premium accent for warnings and highlights."),
    BrandColorSpec("brand_sand", "#F3E8CF", "#2B2518", "identity", "Warm neutral surface that prevents harsh white screens."),
)

BRAND_SURFACES: Sequence[BrandSurfaceSpec] = (
    BrandSurfaceSpec("startup", ("brand_gradient_start", "brand_gradient_end", "brand_on_dark", "splash_progress_chunk"), "Splash/loading identity surface."),
    BrandSurfaceSpec("login", ("login_card_bg", "brand_mark_bg", "primary", "input_focus_bg"), "Login card surface and input focus."),
    BrandSurfaceSpec("activation", ("activation_card_bg", "license_status_bg", "primary", "warning"), "License activation and device status surface."),
    BrandSurfaceSpec("tabs", ("tab_active_bg", "tab_inactive_bg", "tab_active_text", "tab_close_hover_bg"), "Main/sub tab labels and close affordance."),
    BrandSurfaceSpec("menu", ("menu_bg", "menu_active_bg", "menu_active_text", "menu_border"), "Main menu chrome."),
    BrandSurfaceSpec("actions", ("action_bar_bg", "action_primary_bg", "action_secondary_bg", "action_danger_bg"), "Action-bar hierarchy."),
    BrandSurfaceSpec("tables", ("table_header_bg", "table_header_text", "current_cell_bg", "current_cell_border"), "Grid headers and active editable cell."),
    BrandSurfaceSpec("dialogs", ("dialog_bg", "dialog_header_bg", "dialog_footer_bg", "dialog_button_bg"), "Modal windows and confirmation flows."),
    BrandSurfaceSpec("transactions", ("transaction_summary_bg", "transaction_summary_value", "transaction_action_bg", "transaction_close_bg"), "Invoice-like footer summary and bottom action bar."),
    BrandSurfaceSpec("branded_tables", ("table_current_bg", "table_current_border", "table_header_line", "table_row_hover_bg"), "Phase355 branded table and active editable cell surfaces."),
    BrandSurfaceSpec("branded_transaction_footer", ("transaction_footer_surface", "transaction_footer_primary_bg", "transaction_footer_value"), "Phase355 branded invoice footer and bottom commands."),
)

REQUIRED_BRAND_TOKEN_KEYS: Sequence[str] = tuple(
    sorted({key for surface in BRAND_SURFACES for key in surface.token_keys} | {spec.key for spec in BRAND_COLORS})
)


def brand_identity_matrix(tokens: Mapping[str, str] | None = None) -> List[Dict[str, object]]:
    token_map = tokens or {}
    rows: List[Dict[str, object]] = []
    for color in BRAND_COLORS:
        rows.append({
            "kind": "color",
            "key": color.key,
            "role": color.role,
            "description": color.description,
            "required": True,
            "present": color.key in token_map if token_map else True,
        })
    for surface in BRAND_SURFACES:
        missing = [key for key in surface.token_keys if token_map and key not in token_map]
        rows.append({
            "kind": "surface",
            "key": surface.key,
            "role": "surface",
            "description": surface.description,
            "required": True,
            "token_count": len(surface.token_keys),
            "present": not missing,
            "missing": ",".join(missing),
        })
    return rows


def validate_brand_identity_tokens(tokens: Mapping[str, str]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for key in REQUIRED_BRAND_TOKEN_KEYS:
        value = str(tokens.get(key, "")).strip()
        if not value:
            issues.setdefault("missing_tokens", []).append(key)
    return issues


def brand_surface_keys() -> Sequence[str]:
    return tuple(surface.key for surface in BRAND_SURFACES)


__all__ = [
    "IDENTITY_PHASE",
    "IDENTITY_SOURCE_LOGO",
    "BrandColorSpec",
    "BrandSurfaceSpec",
    "BRAND_COLORS",
    "BRAND_SURFACES",
    "REQUIRED_BRAND_TOKEN_KEYS",
    "brand_identity_matrix",
    "brand_surface_keys",
    "validate_brand_identity_tokens",
]
