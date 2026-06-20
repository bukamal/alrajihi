# -*- coding: utf-8 -*-
"""Canonical Material Shell contract.

The materials workspace is not just an item form.  It is the canonical shell for
master material data, units, barcodes, prices, opening stock, barcode-label
printing, list presets and API/network parity.  Keeping this contract data-only
lets CI, PyInstaller builds and future UI policy binders inspect the shell
without importing PyQt widgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from workspace.documents.document_contract import (
    CURRENCY_DISPLAY,
    BRANCH_OPTIONAL,
    NETWORK_REMOTE_AVAILABLE,
    DocumentDescriptor,
    descriptor_for,
    validate_descriptor,
)


MATERIAL_DOCUMENT_TYPE = "material"
MATERIAL_LEGACY_DOCUMENT_TYPES = ("item", "items")
MATERIAL_API_RESOURCE = "/api/items"
MATERIAL_LIST_ROUTE = "items"
MATERIAL_DOCUMENT_CLASS = "features.items.item_editor_tab.MaterialDocumentTab"
MATERIAL_LIST_CLASS = "views.widgets.items_widget.ItemsWidget"
MATERIAL_LOCAL_GATEWAY = "gateways.local.product_gateway.LocalItemGateway"
MATERIAL_REMOTE_GATEWAY = "gateways.remote.product_gateway.RemoteItemGateway"
MATERIAL_SERVER_BLUEPRINT = "items"
MATERIAL_UNIT_PERSISTENCE_POLICY = "atomic_remote_payload_or_local_replace_units"


@dataclass(frozen=True)
class MaterialShellContract:
    """Runtime-independent contract for material document/list surfaces."""

    document_type: str
    descriptor: DocumentDescriptor
    list_class: str
    list_route: str
    api_resource: str
    local_gateway: str
    remote_gateway: str
    server_blueprint: str
    unit_persistence_policy: str
    required_settings_methods: tuple[str, ...]
    required_service_methods: tuple[str, ...]
    required_ui_actions: tuple[str, ...]
    required_i18n_keys: tuple[str, ...]
    legacy_document_types: tuple[str, ...] = MATERIAL_LEGACY_DOCUMENT_TYPES

    def as_matrix(self) -> dict[str, Any]:
        descriptor_warnings = validate_descriptor(self.descriptor)
        return {
            "document_type": self.document_type,
            "shell_family": self.descriptor.shell_family,
            "document_class": self.descriptor.document_class,
            "list_class": self.list_class,
            "api_resource": self.api_resource,
            "network_mode": self.descriptor.network_mode,
            "local_gateway": self.local_gateway,
            "remote_gateway": self.remote_gateway,
            "server_blueprint": self.server_blueprint,
            "settings_scope": self.descriptor.settings_scope,
            "i18n_scope": self.descriptor.i18n_scope,
            "currency_policy": self.descriptor.currency_policy,
            "branch_policy": self.descriptor.branch_policy,
            "can_print": self.descriptor.capabilities.print,
            "can_export": self.descriptor.capabilities.export,
            "can_barcode": self.descriptor.capabilities.barcode,
            "grid_layout": self.descriptor.capabilities.grid_layout,
            "unit_persistence_policy": self.unit_persistence_policy,
            "permissions": dict(self.descriptor.permissions.action_map()),
            "descriptor_warnings": descriptor_warnings,
        }


def material_descriptor() -> DocumentDescriptor:
    descriptor = descriptor_for(MATERIAL_DOCUMENT_TYPE)
    if descriptor is None:
        raise RuntimeError("Material DocumentDescriptor is missing from document_contract.py")
    return descriptor


def material_shell_contract() -> MaterialShellContract:
    descriptor = material_descriptor()
    return MaterialShellContract(
        document_type=MATERIAL_DOCUMENT_TYPE,
        descriptor=descriptor,
        list_class=MATERIAL_LIST_CLASS,
        list_route=MATERIAL_LIST_ROUTE,
        api_resource=MATERIAL_API_RESOURCE,
        local_gateway=MATERIAL_LOCAL_GATEWAY,
        remote_gateway=MATERIAL_REMOTE_GATEWAY,
        server_blueprint=MATERIAL_SERVER_BLUEPRINT,
        unit_persistence_policy=MATERIAL_UNIT_PERSISTENCE_POLICY,
        required_settings_methods=(
            "get_material_settings",
            "get_printing_settings",
            "format_quantity",
            "get_active_profile",
        ),
        required_service_methods=(
            "items_pair",
            "item_by_id",
            "item_by_barcode",
            "add_item",
            "update_item",
            "delete_item",
            "replace_units",
            "item_units",
            "sold_quantities",
            "item_activity_summary",
            "generate_barcode",
            "categories",
        ),
        required_ui_actions=(
            "workspace_save",
            "workspace_print",
            "generate_barcode",
            "generate_barcode_for_selected_unit",
            "scan_barcode_with_camera",
            "add_unit_row",
            "remove_selected_unit_row",
        ),
        required_i18n_keys=(
            "material_title_new",
            "material_title_edit",
            "material_subtitle",
            "material_basic_data",
            "material_pricing_inventory",
            "material_barcode_panel",
            "material_units_panel",
            "material_save_and_print_label",
        ),
    )


def material_shell_matrix() -> dict[str, Any]:
    return material_shell_contract().as_matrix()


def assert_material_shell_contract() -> None:
    contract = material_shell_contract()
    warnings = validate_descriptor(contract.descriptor)
    if warnings:
        raise AssertionError("; ".join(warnings))
    if contract.descriptor.document_type != MATERIAL_DOCUMENT_TYPE:
        raise AssertionError("Material descriptor document_type mismatch")
    if contract.descriptor.api_resource != MATERIAL_API_RESOURCE:
        raise AssertionError("Material API resource mismatch")
    if contract.descriptor.currency_policy != CURRENCY_DISPLAY:
        raise AssertionError("Material shell must respect display currency")
    if contract.descriptor.branch_policy != BRANCH_OPTIONAL:
        raise AssertionError("Material shell branch policy mismatch")
    if contract.descriptor.network_mode != NETWORK_REMOTE_AVAILABLE:
        raise AssertionError("Material shell must be network capable")
    if not contract.descriptor.capabilities.barcode:
        raise AssertionError("Material shell must declare barcode capability")
    if not contract.descriptor.capabilities.grid_layout:
        raise AssertionError("Material shell must declare grid layout capability")
