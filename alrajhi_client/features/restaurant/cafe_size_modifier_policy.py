# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

CAFE_ORDER_TYPE = "cafe_quick_order"
SIZE_ACTION = "size"
ADD_ACTION = "add"
NOTE_ACTION = "note"

DEFAULT_CAFE_SIZES: tuple[dict[str, str], ...] = (
    {"code": "small", "label_key": "restaurant.cafe_size.small", "name": "Small", "price_delta": "0", "kitchen_label": "Small"},
    {"code": "medium", "label_key": "restaurant.cafe_size.medium", "name": "Medium", "price_delta": "0", "kitchen_label": "Medium"},
    {"code": "large", "label_key": "restaurant.cafe_size.large", "name": "Large", "price_delta": "0", "kitchen_label": "Large"},
)

_SIZE_GROUP_KEYWORDS = {
    "size", "cup size", "drink size", "حجم", "الحجم", "مقاس", "المقاس", "größe", "groesse", "bechergröße", "bechergrösse"
}


def decimal_text(value: Any, default: str = "0") -> str:
    try:
        return str(Decimal(str(value if value not in (None, "") else default)))
    except (InvalidOperation, TypeError, ValueError):
        return str(Decimal(default))


def is_cafe_order(session: dict[str, Any] | None) -> bool:
    return str((session or {}).get("order_type") or "").strip().lower() == CAFE_ORDER_TYPE


def is_size_group(group: dict[str, Any] | None) -> bool:
    name = str((group or {}).get("name") or "").strip().lower()
    return any(keyword in name for keyword in _SIZE_GROUP_KEYWORDS)


def split_size_and_modifier_groups(groups: list[dict[str, Any]] | None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    size_group = None
    modifiers: list[dict[str, Any]] = []
    for group in groups or []:
        if size_group is None and is_size_group(group):
            size_group = group
        else:
            modifiers.append(group)
    return size_group, modifiers


def default_size_options() -> list[dict[str, Any]]:
    return [dict(option) for option in DEFAULT_CAFE_SIZES]


def size_options_from_group(group: dict[str, Any] | None) -> list[dict[str, Any]]:
    options = []
    for option in (group or {}).get("options") or []:
        name = str(option.get("name") or "").strip()
        if not name:
            continue
        payload = dict(option)
        payload["group_id"] = payload.get("group_id") or (group or {}).get("id")
        payload["code"] = str(payload.get("code") or name).strip().lower().replace(" ", "_")
        payload["price_delta"] = decimal_text(payload.get("price_delta"), "0")
        payload["kitchen_label"] = payload.get("kitchen_label") or name
        options.append(payload)
    return options or default_size_options()


def normalize_selected_size(size: dict[str, Any] | None) -> dict[str, Any]:
    size = dict(size or {})
    name = str(size.get("name") or size.get("label") or size.get("label_key") or "").strip()
    if not name:
        fallback = DEFAULT_CAFE_SIZES[1]
        size.update(fallback)
        name = fallback["name"]
    size["name"] = name
    size["price_delta"] = decimal_text(size.get("price_delta"), "0")
    size["quantity"] = decimal_text(size.get("quantity"), "1")
    size["action"] = SIZE_ACTION
    size["kitchen_label"] = size.get("kitchen_label") or name
    return size


def normalize_modifier(modifier: dict[str, Any] | None) -> dict[str, Any] | None:
    modifier = dict(modifier or {})
    name = str(modifier.get("name") or modifier.get("label") or "").strip()
    if not name:
        return None
    action = str(modifier.get("action") or ADD_ACTION).strip().lower()
    if action not in {ADD_ACTION, NOTE_ACTION, "remove"}:
        action = ADD_ACTION
    return {
        "group_id": modifier.get("group_id"),
        "option_id": modifier.get("option_id") or modifier.get("id"),
        "name": name,
        "price_delta": decimal_text(modifier.get("price_delta"), "0"),
        "quantity": decimal_text(modifier.get("quantity"), "1"),
        "action": action,
        "kitchen_label": modifier.get("kitchen_label") or name,
    }


def normalize_modifiers(modifiers: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result = []
    for modifier in modifiers or []:
        normalized = normalize_modifier(modifier)
        if normalized:
            result.append(normalized)
    return result


def cafe_line_notes(base_notes: str = "", size: dict[str, Any] | None = None, modifiers: list[dict[str, Any]] | None = None) -> str:
    parts = []
    size_payload = normalize_selected_size(size)
    if size_payload.get("kitchen_label"):
        parts.append(str(size_payload["kitchen_label"]))
    for modifier in normalize_modifiers(modifiers):
        label = str(modifier.get("kitchen_label") or modifier.get("name") or "").strip()
        if label:
            parts.append(label)
    base_notes = str(base_notes or "").strip()
    if base_notes:
        parts.append(base_notes)
    # Preserve a stable, printer-friendly preparation note without currency math.
    return " | ".join(parts)


def build_line_modifiers(size: dict[str, Any] | None, modifiers: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    result = [normalize_selected_size(size)]
    result.extend(normalize_modifiers(modifiers))
    return result
