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


def test_operational_shell_contract_registry_is_valid():
    _prepare_client_import_path()

    from workspace.operational.operational_shell_contract import (
        operational_descriptor_for,
        operational_descriptors,
        validate_operational_descriptors,
    )

    keys = {d.shell_key for d in operational_descriptors()}
    assert {"pos", "restaurant"}.issubset(keys)
    assert validate_operational_descriptors() == []
    assert operational_descriptor_for("pos").document_descriptor.document_type == "pos"
    assert operational_descriptor_for("restaurant").document_descriptor.document_type == "restaurant"


def test_pos_operational_shell_declares_shift_cashbox_warehouse_print_and_currency():
    _prepare_client_import_path()

    from workspace.operational.operational_shell_contract import (
        PRINT_PROFILE_THERMAL80,
        SHIFT_REQUIRED_FOR_CHECKOUT,
        operational_descriptor_for,
    )

    pos = operational_descriptor_for("pos")
    assert pos.currency_policy == "display_currency"
    assert pos.branch_policy == "required"
    assert pos.shift_policy == SHIFT_REQUIRED_FOR_CHECKOUT
    checkout = pos.operation_for("checkout")
    assert checkout.requires_shift is True
    assert checkout.requires_cashbox is True
    assert checkout.requires_warehouse is True
    assert checkout.enabled_setting == "pos/operations/allow_checkout"
    receipt = pos.operation_for("print_receipt")
    assert receipt.print_profile == PRINT_PROFILE_THERMAL80
    assert receipt.permission_action == "pos_print_receipt"


def test_restaurant_operational_shell_declares_session_kitchen_payment_and_printing():
    _prepare_client_import_path()

    from workspace.operational.operational_shell_contract import (
        PRINT_PROFILE_KITCHEN_TICKET,
        PRINT_PROFILE_RESTAURANT_RECEIPT,
        operational_descriptor_for,
    )

    restaurant = operational_descriptor_for("restaurant")
    assert restaurant.api_resource == "/api/restaurant"
    assert restaurant.server_blueprint == "restaurant"
    assert restaurant.operation_for("add_line").requires_session is True
    assert restaurant.operation_for("send_kitchen").category == "kitchen"
    assert restaurant.operation_for("record_payment").category == "payment"
    assert restaurant.operation_for("print_receipt").print_profile == PRINT_PROFILE_RESTAURANT_RECEIPT
    assert restaurant.operation_for("print_kitchen_ticket").print_profile == PRINT_PROFILE_KITCHEN_TICKET


def test_operational_shell_audit_tool_exists_and_writes_matrix():
    tool = ROOT / "tools" / "operational_shell_contract_audit.py"
    assert tool.exists()
    text = tool.read_text(encoding="utf-8")
    assert "operational_shell_contract_matrix.csv" in text
    assert "validate_operational_descriptors" in text


def test_pos_and_restaurant_widgets_are_bound_to_operational_shell_source():
    checks = {
        "alrajhi_client/views/widgets/pos_widget.py": "bind_operational_shell(self, 'pos')",
        "alrajhi_client/views/restaurant/restaurant_pos_widget.py": "bind_operational_shell(self, 'restaurant')",
        "alrajhi_client/views/restaurant/restaurant_dashboard.py": "bind_operational_shell(self, 'restaurant')",
    }
    for rel, marker in checks.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert marker in text, rel


def test_operational_shell_descriptors_do_not_import_pyqt():
    text = (ROOT / "alrajhi_client/workspace/operational/operational_shell_contract.py").read_text(encoding="utf-8")
    assert "PyQt5" not in text
    assert "QWidget" not in text
