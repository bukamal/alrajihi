from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase295_restaurant_operation_policy_covers_new_sensitive_ops():
    source = (ROOT / "alrajhi_client/core/services/restaurant_operation_policy.py").read_text(encoding="utf-8")
    expected = {
        "OP_RESERVE_TABLE": ("restaurant_reserve_table", "restaurant/operations/allow_reserve_table"),
        "OP_CANCEL_RESERVATION": ("restaurant_cancel_reservation", "restaurant/operations/allow_cancel_reservation"),
        "OP_TRANSFER_TABLE": ("restaurant_transfer_table", "restaurant/operations/allow_transfer_table"),
        "OP_MERGE_TABLES": ("restaurant_merge_tables", "restaurant/operations/allow_merge_tables"),
        "OP_MOVE_ORDER_LINE": ("restaurant_move_order_line", "restaurant/operations/allow_move_order_line"),
        "OP_SPLIT_BILL": ("restaurant_split_bill", "restaurant/operations/allow_split_bill"),
        "OP_WAITER_WORKFLOW": ("restaurant_waiter_workflow", "restaurant/operations/allow_waiter_workflow"),
        "OP_KITCHEN_STATION_MANAGE": ("restaurant_kitchen_station_manage", "restaurant/operations/allow_kitchen_station_manage"),
        "OP_MODIFIER_MANAGE": ("restaurant_modifier_manage", "restaurant/operations/allow_modifier_manage"),
        "OP_RECIPE_MANAGE": ("restaurant_recipe_manage", "restaurant/operations/allow_recipe_manage"),
        "OP_DELIVERY_TAKEAWAY": ("restaurant_delivery_takeaway", "restaurant/operations/allow_delivery_takeaway"),
        "OP_PRINTER_MANAGE": ("restaurant_printer_manage", "restaurant/operations/allow_printer_manage"),
        "OP_PRINT_QUEUE": ("restaurant_print_queue", "restaurant/operations/allow_print_queue"),
        "OP_VIEW_ANALYTICS": ("restaurant_view_analytics", "restaurant/operations/allow_view_analytics"),
    }
    for constant, (permission_action, setting_key) in expected.items():
        assert constant in source
        assert permission_action in source
        assert setting_key in source


def test_phase295_permission_service_maps_restaurant_ops_to_rbac_and_security_flags():
    source = (ROOT / "alrajhi_client/core/services/permission_service.py").read_text(encoding="utf-8")
    for literal in [
        "ACTION_RESTAURANT_RESERVE_TABLE",
        "ACTION_RESTAURANT_CANCEL_RESERVATION",
        "ACTION_RESTAURANT_TRANSFER_TABLE",
        "ACTION_RESTAURANT_MERGE_TABLES",
        "ACTION_RESTAURANT_MOVE_ORDER_LINE",
        "ACTION_RESTAURANT_SPLIT_BILL",
        "ACTION_RESTAURANT_WAITER_WORKFLOW",
        "ACTION_RESTAURANT_KITCHEN_STATION_MANAGE",
        "ACTION_RESTAURANT_MODIFIER_MANAGE",
        "ACTION_RESTAURANT_RECIPE_MANAGE",
        "ACTION_RESTAURANT_DELIVERY_TAKEAWAY",
        "ACTION_RESTAURANT_PRINTER_MANAGE",
        "ACTION_RESTAURANT_PRINT_QUEUE",
        "ACTION_RESTAURANT_VIEW_ANALYTICS",
        "restaurant.table.reserve",
        "restaurant.reservation.cancel",
        "restaurant.table.transfer",
        "restaurant.table.merge",
        "restaurant.line.move",
        "restaurant.bill.split",
        "restaurant.kitchen_station.manage",
        "restaurant.recipe.manage",
        "restaurant.print_queue.manage",
        "security/restrict_restaurant_table_transfer_to_admin",
        "security/restrict_restaurant_split_bill_to_admin",
        "security/restrict_restaurant_printer_manage_to_admin",
    ]:
        assert literal in source


def test_phase295_restaurant_service_enforces_governance_before_sensitive_gateway_calls():
    source = (ROOT / "alrajhi_client/core/services/restaurant_service.py").read_text(encoding="utf-8")
    for operation in [
        "OP_RESERVE_TABLE",
        "OP_CANCEL_RESERVATION",
        "OP_TRANSFER_TABLE",
        "OP_MERGE_TABLES",
        "OP_MOVE_ORDER_LINE",
        "OP_SPLIT_BILL",
        "OP_WAITER_WORKFLOW",
        "OP_KITCHEN_STATION_MANAGE",
        "OP_MODIFIER_MANAGE",
        "OP_RECIPE_MANAGE",
        "OP_DELIVERY_TAKEAWAY",
        "OP_PRINTER_MANAGE",
        "OP_PRINT_QUEUE",
        "OP_VIEW_ANALYTICS",
    ]:
        assert operation in source
    assert "def _require_and_log" in source
    assert source.count("self._require_and_log(") >= 20
    assert "restaurant_service.transfer_session" in source
    assert "restaurant_service.merge_sessions" in source
    assert "restaurant_service.create_split_bills" in source
    assert "restaurant_service.upsert_printer" in source


def test_phase295_restaurant_dashboard_table_ops_respect_policy():
    source = (ROOT / "alrajhi_client/views/restaurant/restaurant_dashboard.py").read_text(encoding="utf-8")
    assert "restaurant_operation_policy" in source
    assert "OP_RESERVE_TABLE" in source
    assert "OP_TRANSFER_TABLE" in source
    assert "OP_MERGE_TABLES" in source
    assert "OP_MOVE_ORDER_LINE" in source
    assert "setVisible(allowed_by_settings)" in source
    assert "restaurant_operation_policy.can(restaurant_operation_policy.OP_TRANSFER_TABLE)" in source
    assert "restaurant_operation_policy.require(restaurant_operation_policy.OP_MOVE_ORDER_LINE)" in source


def test_phase295_release_gate_and_translations_are_registered():
    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    translator = (ROOT / "alrajhi_client/i18n/translator.py").read_text(encoding="utf-8")
    assert "RESTAURANT_OPERATION_GOVERNANCE_ENFORCEMENT" in gate
    assert "test_phase295_restaurant_operation_governance_enforcement.py" in gate
    assert "restaurant_operation_governance" in gate
    assert "restaurant_operation_reserve_table" in translator
    assert "restaurant_operation_delivery_takeaway" in translator
    assert "restaurant_operation_governance_extended" in translator
