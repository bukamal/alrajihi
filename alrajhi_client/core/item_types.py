# -*- coding: utf-8 -*-
"""Canonical material/item type helpers.

Visible labels are translated in the UI, but the value persisted in the
business/database layer must be stable.  Earlier translated item-type values
such as "Finished product" or "Fertigprodukt" can still exist in user data, so
manufacturing and filters normalize both canonical and legacy localized values.
"""
from __future__ import annotations

STOCK = 'مخزون'
FINISHED_PRODUCT = 'منتج نهائي'
SERVICE = 'خدمة'

_STOCK_ALIASES = {
    'مخزون', 'stock', 'inventory', 'lagerartikel', 'bestand', 'raw_material', 'raw material',
}
_FINISHED_PRODUCT_ALIASES = {
    'منتج نهائي', 'finished_product', 'finished product', 'finishedproduct', 'fertigprodukt',
    'fertigerzeugnis', 'fertigerzeugnis:', 'finished product:',
}
_SERVICE_ALIASES = {'خدمة', 'service', 'dienstleistung'}


def _norm(value) -> str:
    return str(value or '').strip().casefold().replace('-', '_')


def normalize_item_type(value) -> str:
    key = _norm(value)
    key_space = key.replace('_', ' ')
    if key in _STOCK_ALIASES or key_space in _STOCK_ALIASES:
        return STOCK
    if key in _FINISHED_PRODUCT_ALIASES or key_space in _FINISHED_PRODUCT_ALIASES:
        return FINISHED_PRODUCT
    if key in _SERVICE_ALIASES or key_space in _SERVICE_ALIASES:
        return SERVICE
    return str(value or '')


def is_finished_product(value) -> bool:
    return normalize_item_type(value) == FINISHED_PRODUCT


def is_stock(value) -> bool:
    return normalize_item_type(value) == STOCK


def is_service(value) -> bool:
    return normalize_item_type(value) == SERVICE


def is_bom_component_type(value) -> bool:
    return normalize_item_type(value) in {STOCK, FINISHED_PRODUCT}
