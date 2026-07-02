# -*- coding: utf-8 -*-
"""Central registry for inline quick creation surfaces.

Phase460 keeps quick creation aligned with the rest of the project instead of
letting each screen open ad-hoc dialogs or new tabs.  The registry is deliberately
non-Qt so guards can inspect it without a GUI runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class QuickCreateField:
    name: str
    label_key: str
    widget: str = "line_edit"
    required: bool = False
    placeholder_key: str | None = None


@dataclass(frozen=True)
class QuickCreateDefinition:
    entity_type: str
    title_key: str
    subtitle_key: str
    mode: str
    permission_policy: str
    permission_operation: str
    fields: Tuple[QuickCreateField, ...]
    save_label_key: str = "inline_quick_create_save_select"
    duplicate_policy: str = "select_existing"
    network_boundary: str = "official_service_gateway"


QUICK_CREATE_DEFINITIONS: Dict[str, QuickCreateDefinition] = {
    "category": QuickCreateDefinition(
        entity_type="category",
        title_key="inline_quick_create_category_title",
        subtitle_key="inline_quick_create_category_subtitle",
        mode="compact",
        permission_policy="category_operation_policy",
        permission_operation="create",
        fields=(
            QuickCreateField("name", "category_name", "line_edit", True, "category_name"),
            QuickCreateField("parent_id", "parent_category_label", "combo", False),
            QuickCreateField("description", "description_label", "text_edit", False, "optional_short_description"),
        ),
    ),
    "unit": QuickCreateDefinition(
        entity_type="unit",
        title_key="inline_quick_create_unit_title",
        subtitle_key="inline_quick_create_unit_subtitle",
        mode="compact",
        permission_policy="inventory_operation_policy",
        permission_operation="direct_movement",
        fields=(
            QuickCreateField("unit_name", "unit_name", "line_edit", True, "base_unit_placeholder"),
            QuickCreateField("conversion_factor", "conversion_factor", "decimal", False),
            QuickCreateField("barcode", "barcode", "line_edit", False, "barcode_placeholder"),
        ),
    ),
    "customer": QuickCreateDefinition(
        entity_type="customer",
        title_key="inline_quick_create_customer_title",
        subtitle_key="inline_quick_create_customer_subtitle",
        mode="card",
        permission_policy="party_operation_policy",
        permission_operation="customer_create",
        fields=(
            QuickCreateField("name", "customer_name", "line_edit", True, "customer_name"),
            QuickCreateField("phone", "phone", "line_edit", False),
            QuickCreateField("address", "address", "line_edit", False),
        ),
    ),
    "supplier": QuickCreateDefinition(
        entity_type="supplier",
        title_key="inline_quick_create_supplier_title",
        subtitle_key="inline_quick_create_supplier_subtitle",
        mode="card",
        permission_policy="party_operation_policy",
        permission_operation="supplier_create",
        fields=(
            QuickCreateField("name", "supplier_name", "line_edit", True, "supplier_name"),
            QuickCreateField("phone", "phone", "line_edit", False),
            QuickCreateField("address", "address", "line_edit", False),
        ),
    ),

    "cashbox": QuickCreateDefinition(
        entity_type="cashbox",
        title_key="inline_quick_create_cashbox_title",
        subtitle_key="inline_quick_create_cashbox_subtitle",
        mode="compact",
        permission_policy="finance_operation_policy",
        permission_operation="cashbox_create",
        fields=(
            QuickCreateField("name", "cashbox_name", "line_edit", True, "cashbox_name_placeholder"),
            QuickCreateField("branch_id", "branch_label", "combo", False),
            QuickCreateField("notes", "notes_label", "text_edit", False, "optional_short_description"),
        ),
    ),
    "bank_account": QuickCreateDefinition(
        entity_type="bank_account",
        title_key="inline_quick_create_bank_account_title",
        subtitle_key="inline_quick_create_bank_account_subtitle",
        mode="card",
        permission_policy="finance_operation_policy",
        permission_operation="bank_create",
        fields=(
            QuickCreateField("bank_name", "bank_label", "line_edit", True, "bank_name_placeholder"),
            QuickCreateField("account_name", "account_name_label", "line_edit", False, "bank_account_name_placeholder"),
            QuickCreateField("account_number", "account_number_label", "line_edit", False, "bank_account_number_placeholder"),
            QuickCreateField("branch_id", "branch_label", "combo", False),
            QuickCreateField("notes", "notes_label", "text_edit", False, "optional_short_description"),
        ),
    ),
    "item": QuickCreateDefinition(
        entity_type="item",
        title_key="inline_quick_create_item_title",
        subtitle_key="inline_quick_create_item_subtitle",
        mode="drawer",
        permission_policy="permission_service",
        permission_operation="edit_items",
        fields=(
            QuickCreateField("name", "item_name_label", "line_edit", True, "material_name_placeholder"),
            QuickCreateField("barcode", "barcode", "line_edit", False, "barcode_placeholder"),
            QuickCreateField("category_id", "category_label", "combo", False),
            QuickCreateField("unit", "base_unit_label", "line_edit", True, "base_unit_placeholder"),
            QuickCreateField("selling_price", "selling_price", "decimal", False),
            QuickCreateField("purchase_price", "purchase_price", "decimal", False),
        ),
    ),
}


def definition_for(entity_type: str) -> QuickCreateDefinition:
    key = str(entity_type or "").strip().lower()
    if key not in QUICK_CREATE_DEFINITIONS:
        raise KeyError(f"Unknown inline quick create entity: {entity_type}")
    return QUICK_CREATE_DEFINITIONS[key]


def supported_entities() -> Tuple[str, ...]:
    return tuple(QUICK_CREATE_DEFINITIONS.keys())
