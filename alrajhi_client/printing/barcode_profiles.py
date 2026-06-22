# -*- coding: utf-8 -*-
"""Settings-driven barcode label profile contract.

Phase 338 foundation: barcode labels for materials, apparel variants,
restaurant and cafe must not be separate print islands.  This module resolves
one profile id to the same Browser-HTML label renderer while keeping profile
specific fields/settings outside individual screens.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

try:
    from workspace.registry import BARCODE_PRINT_PROFILES, WorkspaceBarcodeProfileSpec
except Exception:  # pragma: no cover - import guard for packaging probes
    BARCODE_PRINT_PROFILES = {}
    WorkspaceBarcodeProfileSpec = object  # type: ignore


def _settings_get(key: str, default: Any = "") -> Any:
    try:
        from core.services.settings_service import settings_service
        return settings_service.get(key, default)
    except Exception:
        return default


def _printing_settings() -> Dict[str, Any]:
    try:
        from core.services.settings_service import settings_service
        return settings_service.get_printing_settings()
    except Exception:
        return {}


def _bool_value(value: Any, default: bool = True) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: Any, default: int, minimum: int = 1, maximum: int = 999) -> int:
    try:
        number = int(value)
    except Exception:
        number = int(default)
    return min(max(number, minimum), maximum)


PROFILE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "items.default": {
        "label_size": "50x30",
        "columns": 2,
        "show_qr": True,
        "show_name": True,
        "show_price": True,
        "show_variant_color_size": False,
        "show_variant_code": False,
        "show_section": False,
        "show_table_zone": False,
        "show_modifier_group": False,
    },
    "apparel.variant_labels": {
        "label_size": "50x30",
        "columns": 2,
        "show_qr": True,
        "show_name": True,
        "show_price": True,
        "show_variant_color_size": True,
        "show_variant_code": True,
        "show_section": False,
        "show_table_zone": False,
        "show_modifier_group": False,
    },
    "restaurant.menu_items": {
        "label_size": "50x30",
        "columns": 2,
        "show_qr": True,
        "show_name": True,
        "show_price": True,
        "show_variant_color_size": False,
        "show_variant_code": False,
        "show_section": True,
        "show_table_zone": False,
        "show_modifier_group": False,
    },
    "restaurant.table_labels": {
        "label_size": "60x40",
        "columns": 2,
        "show_qr": True,
        "show_name": True,
        "show_price": False,
        "show_variant_color_size": False,
        "show_variant_code": False,
        "show_section": False,
        "show_table_zone": True,
        "show_modifier_group": False,
    },
    "cafe.products": {
        "label_size": "50x30",
        "columns": 2,
        "show_qr": True,
        "show_name": True,
        "show_price": True,
        "show_variant_color_size": False,
        "show_variant_code": False,
        "show_section": False,
        "show_table_zone": False,
        "show_modifier_group": False,
        "show_size": True,
    },
    "cafe.modifier_labels": {
        "label_size": "40x30",
        "columns": 3,
        "show_qr": True,
        "show_name": True,
        "show_price": True,
        "show_variant_color_size": False,
        "show_variant_code": False,
        "show_section": False,
        "show_table_zone": False,
        "show_modifier_group": True,
    },
}


PROFILE_BOOL_FIELDS = (
    "show_company",
    "show_logo",
    "show_qr",
    "show_name",
    "show_price",
    "show_barcode_text",
    "show_variant_color_size",
    "show_variant_code",
    "show_section",
    "show_table_zone",
    "show_modifier_group",
    "show_size",
)


def barcode_profile(profile_id: str = "items.default") -> WorkspaceBarcodeProfileSpec:
    """Return a registered profile, falling back to material labels."""
    return BARCODE_PRINT_PROFILES.get(profile_id) or BARCODE_PRINT_PROFILES["items.default"]


def barcode_profile_settings_prefix(profile_id: str = "items.default") -> str:
    return barcode_profile(profile_id).settings_prefix


def barcode_profile_options(profile_id: str = "items.default", overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Resolve global + per-profile barcode settings for the HTML renderer."""
    profile = barcode_profile(profile_id)
    prefix = profile.settings_prefix
    global_cfg = _printing_settings()
    defaults = dict(PROFILE_DEFAULTS.get(profile.profile_id, PROFILE_DEFAULTS["items.default"]))
    opts: Dict[str, Any] = {
        "profile_id": profile.profile_id,
        "template_id": _settings_get(f"{prefix}/template_id", profile.default_template_id) or profile.default_template_id,
        "label_size": _settings_get(f"{prefix}/label_size", defaults.get("label_size", global_cfg.get("barcode_label_size", "50x30"))),
        "symbology": str(_settings_get(f"{prefix}/symbology", global_cfg.get("barcode_symbology", "AUTO")) or "AUTO").upper(),
        "columns": _int_value(_settings_get(f"{prefix}/columns", defaults.get("columns", global_cfg.get("barcode_columns", 2))), 2, 1, 4),
        "copies": _int_value(_settings_get(f"{prefix}/copies", global_cfg.get("barcode_copies", 1)), 1, 1, 999),
        "printable_fields": tuple(profile.printable_fields),
        "supports_multi_print": bool(profile.supports_multi_print),
        "browser_html_only": bool(profile.browser_html_only),
    }
    bool_defaults = {
        "show_company": global_cfg.get("barcode_show_company", True),
        "show_logo": global_cfg.get("barcode_show_logo", global_cfg.get("show_logo", True)),
        "show_qr": defaults.get("show_qr", global_cfg.get("barcode_show_qr", True)),
        "show_name": defaults.get("show_name", global_cfg.get("barcode_show_name", True)),
        "show_price": defaults.get("show_price", global_cfg.get("barcode_show_price", True)),
        "show_barcode_text": global_cfg.get("barcode_show_text", True),
        "show_variant_color_size": defaults.get("show_variant_color_size", False),
        "show_variant_code": defaults.get("show_variant_code", False),
        "show_section": defaults.get("show_section", False),
        "show_table_zone": defaults.get("show_table_zone", False),
        "show_modifier_group": defaults.get("show_modifier_group", False),
        "show_size": defaults.get("show_size", False),
    }
    for key in PROFILE_BOOL_FIELDS:
        opts[key] = _bool_value(_settings_get(f"{prefix}/{key}", bool_defaults.get(key, False)), bool_defaults.get(key, False))
    if overrides:
        opts.update({k: v for k, v in overrides.items() if v is not None})
        opts["profile_id"] = str(opts.get("profile_id") or profile.profile_id)
    return opts


def _first_text(item: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(item.get(key, "") or "").strip()
        if value:
            return value
    return ""


def normalize_barcode_item(item: Dict[str, Any], profile_id: str = "items.default") -> Dict[str, Any]:
    """Normalize sector-specific rows to a generic printable label payload."""
    profile = barcode_profile(profile_id)
    row = dict(item or {})
    scope = profile.item_scope
    if scope == "apparel_variant":
        row.setdefault("name", _first_text(row, "item_name", "base_item_name", "product_name", "name"))
        row.setdefault("variant_color", _first_text(row, "variant_color", "color"))
        row.setdefault("variant_size", _first_text(row, "variant_size", "size"))
        row.setdefault("variant_code", _first_text(row, "variant_code", "code", "sku"))
        # Apparel labels must print the variant barcode; never fall back to the
        # parent material barcode if the row carries a matched variant code.
        row["barcode"] = _first_text(row, "variant_barcode", "matched_barcode", "barcode")
        row.setdefault("price", _first_text(row, "price", "sale_price", "selling_price"))
    elif scope == "restaurant_menu_item":
        row.setdefault("name", _first_text(row, "menu_item", "item_name", "name"))
        row.setdefault("section", _first_text(row, "section", "category", "group"))
        row.setdefault("price", _first_text(row, "price", "selling_price"))
    elif scope == "restaurant_table":
        row.setdefault("name", _first_text(row, "table_number", "table_name", "name"))
        row.setdefault("zone", _first_text(row, "zone", "section", "area"))
        row.setdefault("qr_value", _first_text(row, "qr", "qr_value", "barcode", "table_code", "name"))
        row.setdefault("barcode", _first_text(row, "barcode", "table_code"))
    elif scope == "cafe_product":
        row.setdefault("name", _first_text(row, "product_name", "menu_item", "item_name", "name"))
        row.setdefault("size", _first_text(row, "size", "cup_size", "variant_size"))
        row.setdefault("price", _first_text(row, "price", "selling_price"))
    elif scope == "cafe_modifier":
        row.setdefault("name", _first_text(row, "modifier_name", "name"))
        row.setdefault("group", _first_text(row, "group", "modifier_group", "category"))
        row.setdefault("price", _first_text(row, "price", "selling_price"))
    else:
        row.setdefault("name", _first_text(row, "item_name", "product_name", "name"))
        row.setdefault("price", _first_text(row, "price", "selling_price"))
    row.setdefault("copies", 1)
    return row


def normalize_barcode_items(items: Iterable[Dict[str, Any]], profile_id: str = "items.default") -> List[Dict[str, Any]]:
    return [normalize_barcode_item(dict(item or {}), profile_id) for item in (items or [])]


__all__ = [
    "PROFILE_DEFAULTS",
    "barcode_profile",
    "barcode_profile_settings_prefix",
    "barcode_profile_options",
    "normalize_barcode_item",
    "normalize_barcode_items",
]
