# -*- coding: utf-8 -*-
"""Restaurant recipe/material consumption policy.

The restaurant workflow can sell finished menu items while inventory must be
reduced from their underlying components.  This module contains the arithmetic
and idempotency key rules shared by the local gateway and the server repository.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

RESTAURANT_CONSUME_MOVEMENT_TYPE = "restaurant_consume"
RESTAURANT_RECIPE_SOURCE = "restaurant_recipe"
MANUFACTURING_BOM_SOURCE = "manufacturing_bom"


def decimal_value(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def positive_decimal(value: Any, default: str = "1") -> Decimal:
    result = decimal_value(value, default)
    return result if result > Decimal("0") else Decimal(default)


def required_component_quantity(
    sold_quantity: Any,
    component_quantity: Any,
    recipe_yield_quantity: Any = "1",
    conversion_factor: Any = "1",
    waste_percent: Any = "0",
) -> Decimal:
    """Return component base quantity required for a sold restaurant line.

    ``component_quantity`` is the quantity specified on the restaurant recipe or
    BOM line. ``recipe_yield_quantity`` is the output quantity produced by that
    recipe/BOM. ``conversion_factor`` converts a BOM secondary-unit line into
    the component base unit. ``waste_percent`` follows the manufacturing module
    convention where 10% is stored as 0.10.
    """
    sold = decimal_value(sold_quantity, "0")
    component = decimal_value(component_quantity, "0")
    output_qty = positive_decimal(recipe_yield_quantity, "1")
    factor = positive_decimal(conversion_factor, "1")
    waste = Decimal("1") + decimal_value(waste_percent, "0")
    return sold * component * factor * waste / output_qty


def consumption_source_key(source_type: str, session_id: int, order_line_id: int, component_id: Any) -> str:
    component = str(component_id if component_id not in (None, "") else "component")
    return f"restaurant:{source_type}:{int(session_id)}:{int(order_line_id)}:{component}"


def movement_note(source_type: str, session_id: int, order_line_id: int, invoice_id: int | None = None) -> str:
    ref = f"session {int(session_id)} / line {int(order_line_id)}"
    if invoice_id:
        ref = f"invoice {int(invoice_id)} / {ref}"
    if source_type == MANUFACTURING_BOM_SOURCE:
        return f"Restaurant BOM component consumption - {ref}"
    return f"Restaurant recipe component consumption - {ref}"
