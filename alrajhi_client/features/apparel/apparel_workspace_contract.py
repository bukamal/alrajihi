# -*- coding: utf-8 -*-
"""Apparel workspace contract built on item variants.

Phase 316 deliberately adds a visible apparel workspace without creating a
separate apparel engine.  Color/size identity remains on item_variants and all
lookups go through ProductService/Gateway.
"""
from __future__ import annotations

from typing import Mapping

APPAREL_PAGE_ID = "apparel"
APPAREL_SETTINGS_KEY = "apparel/enabled"
APPAREL_ENGINE_BACKING = "product_variants"
APPAREL_VARIANT_SCOPE = "variant"
APPAREL_MATRIX_SCOPE = "color_size_matrix"
APPAREL_BULK_BUILDER = "product_service_create_missing_variants"
APPAREL_VISIBLE_COLUMNS = (
    "item",
    "color",
    "size",
    "sku",
    "barcode",
    "quantity",
    "reorder_level",
    "sale_price",
    "status",
)
APPAREL_FORBIDDEN_ENGINE_FILES = (
    "apparel_gateway.py",
    "apparel_repository.py",
    "apparel_dao.py",
)


def apparel_page_enabled_from_settings(settings: Mapping[str, object] | None) -> bool:
    settings = settings or {}
    if APPAREL_SETTINGS_KEY in settings:
        return str(settings.get(APPAREL_SETTINGS_KEY)).strip().lower() in {"1", "true", "yes", "on", "y", "نعم"}
    apparel = settings.get("apparel")
    if isinstance(apparel, Mapping) and "enabled" in apparel:
        return str(apparel.get("enabled")).strip().lower() in {"1", "true", "yes", "on", "y", "نعم"}
    return True


def apparel_workspace_contract() -> dict[str, object]:
    return {
        "page_id": APPAREL_PAGE_ID,
        "settings_key": APPAREL_SETTINGS_KEY,
        "engine_backing": APPAREL_ENGINE_BACKING,
        "variant_scope": APPAREL_VARIANT_SCOPE,
        "matrix_scope": APPAREL_MATRIX_SCOPE,
        "bulk_builder": APPAREL_BULK_BUILDER,
        "visible_columns": list(APPAREL_VISIBLE_COLUMNS),
        "uses_product_service": True,
        "forbidden_engine_files": list(APPAREL_FORBIDDEN_ENGINE_FILES),
    }


def apparel_uses_product_variant_engine() -> bool:
    return True
