# -*- coding: utf-8 -*-
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _prepare_client_import_path():
    import sys
    client = ROOT / "alrajhi_client"
    if str(client) not in sys.path:
        sys.path.insert(0, str(client))
    existing = sys.modules.get("workspace")
    if existing is not None and not hasattr(existing, "__path__"):
        sys.modules.pop("workspace", None)


def test_list_workspace_contract_registry_is_complete_and_valid():
    _prepare_client_import_path()

    from workspace.lists.list_workspace_contract import (
        list_descriptor_for,
        list_descriptors,
        validate_list_descriptors,
    )

    required = {
        "sales_invoices",
        "purchase_invoices",
        "sales_returns",
        "purchase_returns",
        "materials",
        "categories",
        "customers",
        "suppliers",
        "vouchers",
        "cashboxes",
        "warehouses",
        "warehouse_transfers",
        "branches",
    }
    keys = {d.list_key for d in list_descriptors()}
    assert required.issubset(keys)
    assert validate_list_descriptors() == []
    assert list_descriptor_for("materials").document_descriptor.document_type == "material"
    assert list_descriptor_for("sales_invoices").permission_for("print") == "sales_invoices.print"


def test_list_workspace_actions_map_to_document_permissions():
    _prepare_client_import_path()

    from workspace.lists.list_workspace_contract import list_descriptor_for

    customers = list_descriptor_for("customers")
    assert customers.permission_for("open") == customers.document_descriptor.permissions.view
    assert customers.permission_for("search") == customers.document_descriptor.permissions.view
    assert customers.permission_for("create") == customers.document_descriptor.permissions.create
    assert customers.permission_for("update") == customers.document_descriptor.permissions.update

    vouchers = list_descriptor_for("vouchers")
    assert vouchers.capabilities.print is True
    assert vouchers.permission_for("print") == "vouchers.print"
    assert vouchers.currency_policy != "none"


def test_list_workspace_audit_tool_exists_and_writes_matrix():
    tool = ROOT / "tools" / "list_workspace_contract_audit.py"
    assert tool.exists()
    text = tool.read_text(encoding="utf-8")
    assert "list_workspace_contract_matrix.csv" in text
    assert "validate_list_descriptors" in text


def test_key_widgets_are_bound_to_list_workspace_contract_source():
    checks = {
        "alrajhi_client/views/widgets/items_widget.py": "bind_list_workspace(self, 'materials')",
        "alrajhi_client/views/widgets/invoices_widget.py": "bind_list_workspace(self, 'sales_invoices')",
        "alrajhi_client/views/widgets/returns_widget.py": "bind_list_workspace(self, 'sales_returns')",
        "alrajhi_client/views/widgets/customers_widget.py": "bind_list_workspace(self, 'customers')",
        "alrajhi_client/views/widgets/suppliers_widget.py": "bind_list_workspace(self, 'suppliers')",
        "alrajhi_client/views/widgets/vouchers_widget.py": "bind_list_workspace(self, 'vouchers')",
    }
    for rel, marker in checks.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert marker in text, rel
