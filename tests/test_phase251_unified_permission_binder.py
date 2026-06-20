# -*- coding: utf-8 -*-
from pathlib import Path
import importlib.util
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "alrajhi_client/workspace/documents/document_contract.py"
BINDER_PATH = ROOT / "alrajhi_client/workspace/documents/document_permission_binder.py"


def _load_modules():
    # Avoid importing workspace.documents.__init__, because that imports PyQt.
    sys.modules.setdefault("workspace", types.ModuleType("workspace"))
    pkg = types.ModuleType("workspace.documents")
    pkg.__path__ = [str(BINDER_PATH.parent)]
    sys.modules["workspace.documents"] = pkg

    spec = importlib.util.spec_from_file_location("workspace.documents.document_contract", CONTRACT_PATH)
    contract = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = contract
    spec.loader.exec_module(contract)

    spec2 = importlib.util.spec_from_file_location("workspace.documents.document_permission_binder", BINDER_PATH)
    binder = importlib.util.module_from_spec(spec2)
    assert spec2.loader is not None
    sys.modules[spec2.name] = binder
    spec2.loader.exec_module(binder)
    return contract, binder


class DummyActionBar:
    def __init__(self):
        self.enabled = {}

    def set_action_enabled(self, action, enabled):
        self.enabled[action] = bool(enabled)


class DummyButton:
    def __init__(self):
        self.enabled = True
        self.tooltip = ""

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)

    def setToolTip(self, text):
        self.tooltip = str(text)


class DummyWidget:
    def __init__(self):
        self.save_btn = DummyButton()
        self.bottom_print_btn = DummyButton()
        self.bottom_export_btn = DummyButton()


def test_phase251_permission_binder_is_data_only():
    text = BINDER_PATH.read_text(encoding="utf-8")
    assert "from PyQt5" not in text
    assert "class DocumentPermissionBinder" in text
    assert "apply_to_action_bar" in text


def test_phase251_transaction_save_uses_create_for_new_and_update_for_existing():
    contract, binder_mod = _load_modules()
    descriptor = contract.descriptor_for("purchase_invoice")
    binder = binder_mod.DocumentPermissionBinder(descriptor, checker=lambda key: key != "purchase_invoices.update")

    assert binder.permission_key_for("save", document_id=None) == "purchase_invoices.create"
    assert binder.permission_key_for("save", document_id=123) == "purchase_invoices.update"
    assert binder.can("save", document_id=None) is True
    assert binder.can("save", document_id=123) is False


def test_phase251_action_bar_follows_descriptor_capabilities_and_permissions():
    contract, binder_mod = _load_modules()
    descriptor = contract.descriptor_for("purchase_invoice")
    binder = binder_mod.DocumentPermissionBinder(descriptor, checker=lambda key: key != "purchase_invoices.print")
    bar = DummyActionBar()

    binder.apply_to_action_bar(bar, document_id=None)

    assert bar.enabled["save"] is True
    assert bar.enabled["print"] is False
    assert bar.enabled["export"] is True


def test_phase251_widget_buttons_are_bound_without_requiring_one_visual_shell():
    contract, binder_mod = _load_modules()
    descriptor = contract.descriptor_for("voucher")
    binder = binder_mod.DocumentPermissionBinder(descriptor, checker=lambda key: key != "vouchers.export")
    widget = DummyWidget()

    states = binder.apply_to_widget_buttons(widget, document_id=42)

    assert states["save"] is True
    assert states["print"] is True
    assert states["export"] is False
    assert widget.save_btn.enabled is True
    assert widget.bottom_print_btn.enabled is True
    assert widget.bottom_export_btn.enabled is False
    assert "vouchers.export" in widget.bottom_export_btn.tooltip


def test_phase251_unknown_permission_remains_backward_compatible():
    _contract, binder_mod = _load_modules()
    assert binder_mod.document_permission_allowed("custom.future.permission") is True
