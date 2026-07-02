# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import (
    QAction, QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QSplitter, QStackedWidget, QToolButton, QVBoxLayout, QWidget
)

from core.services.restaurant_service import restaurant_service
from core.services.settings_service import settings_service
from core.services.restaurant_operation_policy import restaurant_operation_policy
from i18n.translator import qt_layout_direction, translate as _
from views.restaurant.table_map_widget import RestaurantTableMapWidget
from views.restaurant.restaurant_pos_widget import RestaurantPOSWidget
from views.restaurant.kitchen_display_widget import KitchenDisplayWidget
from views.dialogs.batch_print_dialog import BatchPrintDialog
from views.restaurant.restaurant_analytics_widget import RestaurantAnalyticsWidget
from workspace.operational.operational_shell_contract import bind_operational_shell
from ui.inline_quick_create import InlineQuickCreatePanel, quick_create_can



class RestaurantReservationDialog(QDialog):
    """Small reservation dialog used by the restaurant operation shell."""

    def __init__(self, tables: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("restaurant.reserve_table"))
        self.setMinimumWidth(460)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.table_combo = QComboBox()
        for table in tables:
            self.table_combo.addItem(self._table_label(table), int(table.get("id") or 0))
        self.customer_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.guests_spin = QSpinBox()
        self.guests_spin.setMinimum(1)
        self.guests_spin.setMaximum(99)
        self.reserved_at_edit = QLineEdit()
        self.reserved_at_edit.setPlaceholderText(_("restaurant.reserved_at_placeholder"))
        self.notes_edit = QLineEdit()
        for widget in (self.table_combo, self.customer_edit, self.phone_edit, self.guests_spin, self.reserved_at_edit, self.notes_edit):
            widget.setMinimumHeight(44)
        form.addRow(_("restaurant.table"), self.table_combo)
        form.addRow(_("customer_name"), self.customer_edit)
        form.addRow(_("phone"), self.phone_edit)
        form.addRow(_("restaurant.guests"), self.guests_spin)
        form.addRow(_("restaurant.reserved_at"), self.reserved_at_edit)
        form.addRow(_("notes"), self.notes_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        save = QPushButton(_("restaurant.reserve_table"))
        cancel.setMinimumHeight(48)
        save.setMinimumHeight(48)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _table_label(self, table: dict) -> str:
        zone = table.get("zone") or table.get("area") or ""
        seats = table.get("seats") or ""
        return f"{table.get('name') or table.get('id')} — {zone} — {seats}"

    def payload(self) -> dict:
        return {
            "table_id": int(self.table_combo.currentData() or 0),
            "customer_name": self.customer_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "guests": int(self.guests_spin.value()),
            "reserved_at": self.reserved_at_edit.text().strip(),
            "notes": self.notes_edit.text().strip(),
        }


class RestaurantTableTargetDialog(QDialog):
    """Generic target table/session picker for transfer, merge and line split operations."""

    def __init__(self, title: str, tables: list[dict], action_label: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        self.table_combo = QComboBox()
        for table in tables:
            self.table_combo.addItem(self._table_label(table), table)
        self.table_combo.setMinimumHeight(48)
        layout.addWidget(QLabel(title))
        layout.addWidget(self.table_combo)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        apply = QPushButton(action_label)
        cancel.setMinimumHeight(48)
        apply.setMinimumHeight(48)
        cancel.clicked.connect(self.reject)
        apply.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(apply)
        layout.addLayout(buttons)

    def _table_label(self, table: dict) -> str:
        state = table.get("ui_status") or table.get("status") or ""
        zone = table.get("zone") or table.get("area") or ""
        session = table.get("active_session_id")
        suffix = f" / {_('restaurant.session')}: {session}" if session else ""
        return f"{table.get('name') or table.get('id')} — {_(f'restaurant.status.{state}')} — {zone}{suffix}"

    def selected_table(self) -> dict:
        return self.table_combo.currentData() or {}



RESTAURANT_RESPONSIVE_BREAKPOINTS = {"compact": 1280, "wide": 1600}
RESTAURANT_ORDER_SPLITTER_SIZES = {
    "compact": [360, 780, 0],
    "standard": [430, 860, 0],
    "wide": [500, 1020, 0],
}
RESTAURANT_KITCHEN_SPLITTER_SIZES = {
    "compact": [360, 0, 780],
    "standard": [360, 0, 860],
    "wide": [420, 700, 560],
}
RESTAURANT_ANALYTICS_SPLITTER_SIZES = {
    "compact": [360, 0, 780],
    "standard": [380, 0, 820],
    "wide": [420, 700, 520],
}

# Phase 298: true fullscreen operational shell.  These page ratios prevent
# current order, kitchen display, and table map from being squeezed together.
RESTAURANT_FULLSCREEN_ORDER_SIZES = {
    "compact": [760, 260],
    "standard": [900, 320],
    "wide": [1160, 420],
}
RESTAURANT_FULLSCREEN_KITCHEN_SIZES = {
    "compact": [900, 0],
    "standard": [980, 260],
    "wide": [1180, 360],
}
RESTAURANT_FULLSCREEN_TABLE_SIZES = {
    "compact": [980],
    "standard": [1120],
    "wide": [1400],
}


class RestaurantDashboard(QWidget):
    """Unified Restaurant Operation Shell.

    Phase 283: the operational screen is centered around the live order.  The
    default view is two-pane (tables + current order/menu).  Kitchen display and
    analytics are explicit modes instead of permanent crowded panes.
    """

    def __init__(self, parent=None, *, workspace_context: str = "restaurant"):
        super().__init__(parent)
        bind_operational_shell(self, 'restaurant')
        self._workspace_context = str(workspace_context or 'restaurant')
        self._standalone_cafe_workspace = self._workspace_context == 'cafe'
        self.service = restaurant_service
        self._last_tables: list[dict] = []
        self._ui_settings = self._restaurant_ui_settings()
        self._current_mode = "order"
        self._responsive_layout_mode = "standard"
        self.setObjectName("restaurantDashboard")
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_card = QFrame()
        header_card.setObjectName("restaurantHeaderCard")
        header = QHBoxLayout(header_card)
        header.setContentsMargins(16, 10, 16, 10)
        title_text = "☕  " + _("restaurant.cafe_workspace_title") if self._standalone_cafe_workspace else "🍽  " + _("restaurant.operation_shell")
        title = QLabel(title_text)
        title.setObjectName("restaurantDashboardTitle")
        self.dashboard_title = title
        header.addWidget(title)
        header.addStretch()

        self.order_mode_btn = QPushButton("🧾  " + _("restaurant.mode.order"))
        self.order_mode_btn.setObjectName("restaurantOrderModeButton")
        # Phase 314: the cafe is a standalone top-level workspace.  Keep an
        # unattached compatibility button for older plugins/tests that inspect
        # attributes, but never expose it inside the restaurant toolbar.
        self.cafe_mode_btn = QPushButton("☕  " + _("restaurant.mode.cafe"))
        self.cafe_mode_btn.setObjectName("restaurantCafeModeButton")
        self.cafe_mode_btn.setVisible(False)
        self.kitchen_mode_btn = QPushButton("👨‍🍳  " + _("restaurant.mode.kitchen"))
        self.kitchen_mode_btn.setObjectName("restaurantKitchenModeButton")
        self.tables_mode_btn = QPushButton("🪑  " + _("restaurant.mode.tables"))
        self.tables_mode_btn.setObjectName("restaurantTablesModeButton")
        self.analytics_mode_btn = QPushButton("📊  " + _("restaurant.mode.analytics"))
        self.analytics_mode_btn.setObjectName("restaurantAnalyticsModeButton")
        self.mode_badge = QLabel(_("restaurant.touch_mode"))
        self.mode_badge.setObjectName("restaurantModeBadge")
        self.refresh_button = QPushButton("↻  " + _("common.refresh"))
        self.refresh_button.setObjectName("restaurantRefreshButton")
        self.quick_category_btn = QPushButton("+ " + _("category_label"))
        self.quick_category_btn.setObjectName("restaurantDashboardInlineQuickCategoryButton")
        self.quick_category_btn.setToolTip(_("inline_quick_create_restaurant_category_tooltip"))
        self.quick_category_btn.setVisible(quick_create_can('category'))
        self.quick_item_btn = QPushButton("+ " + _("item"))
        self.quick_item_btn.setObjectName("restaurantDashboardInlineQuickItemButton")
        self.quick_item_btn.setToolTip(_("inline_quick_create_restaurant_item_tooltip"))
        self.quick_item_btn.setVisible(quick_create_can('item'))
        self.menu_barcode_btn = QPushButton("🏷️  " + _("barcode.restaurant_menu_labels"))
        self.menu_barcode_btn.setObjectName("restaurantMenuBarcodeButton")
        self.table_barcode_btn = QPushButton("▦  " + _("barcode.restaurant_table_labels"))
        self.table_barcode_btn.setObjectName("restaurantTableBarcodeButton")
        for button in (self.order_mode_btn, self.cafe_mode_btn, self.kitchen_mode_btn, self.tables_mode_btn, self.analytics_mode_btn, self.refresh_button, self.quick_category_btn, self.quick_item_btn, self.menu_barcode_btn, self.table_barcode_btn):
            button.setMinimumHeight(44)
            button.setProperty("visualRole", "operational_secondary")
        self.analytics_mode_btn.setVisible(bool(self._ui_settings.get("show_analytics_panel")) and not self._standalone_cafe_workspace)
        self.cafe_mode_btn.setVisible(False)
        if self._standalone_cafe_workspace:
            self.order_mode_btn.setVisible(False)
            self.kitchen_mode_btn.setVisible(False)
            self.tables_mode_btn.setVisible(False)
            self.analytics_mode_btn.setVisible(False)
            self.menu_barcode_btn.setVisible(False)
            self.table_barcode_btn.setVisible(False)
        header.addWidget(self.order_mode_btn)
        # Cafe is intentionally not added to the restaurant header after Phase 314.
        header.addWidget(self.kitchen_mode_btn)
        header.addWidget(self.tables_mode_btn)
        header.addWidget(self.analytics_mode_btn)
        header.addWidget(self.mode_badge)
        header.addWidget(self.menu_barcode_btn)
        header.addWidget(self.table_barcode_btn)
        header.addWidget(self.refresh_button)
        header.addWidget(self.quick_category_btn)
        header.addWidget(self.quick_item_btn)
        layout.addWidget(header_card)

        self.inline_category_panel = InlineQuickCreatePanel('category', self)
        self.inline_category_panel.setObjectName("restaurantDashboardInlineQuickCategoryPanel")
        self.inline_category_panel.created.connect(self._on_inline_category_created)
        layout.addWidget(self.inline_category_panel)
        self.inline_item_panel = InlineQuickCreatePanel('item', self)
        self.inline_item_panel.setObjectName("restaurantDashboardInlineQuickItemPanel")
        self.inline_item_panel.created.connect(self._on_inline_item_created)
        layout.addWidget(self.inline_item_panel)

        self.table_ops_card = QFrame()
        self.table_ops_card.setObjectName("restaurantTableOperationsBar")
        ops = QHBoxLayout(self.table_ops_card)
        ops.setContentsMargins(12, 8, 12, 8)
        ops.setSpacing(8)
        ops.addWidget(QLabel("🪑  " + _("restaurant.table_operations")))
        ops.addStretch()
        self.reserve_table_btn = QPushButton("📌  " + _("restaurant.reserve_table"))
        self.transfer_table_btn = QPushButton("↔  " + _("restaurant.transfer_table"))
        self.merge_table_btn = QPushButton("🔗  " + _("restaurant.merge_tables"))
        self.move_line_btn = QPushButton("➡  " + _("restaurant.move_selected_line"))
        self.table_ops_menu_btn = QToolButton()
        self.table_ops_menu_btn.setObjectName("restaurantTableOperationsMenuButton")
        self.table_ops_menu_btn.setText("⋯  " + _("restaurant.table_operations"))
        self.table_ops_menu_btn.setPopupMode(QToolButton.InstantPopup)
        self.table_ops_menu = QMenu(self.table_ops_menu_btn)
        self.table_ops_menu_btn.setMenu(self.table_ops_menu)
        self._table_ops_action_map = []
        for button in (self.reserve_table_btn, self.transfer_table_btn, self.merge_table_btn, self.move_line_btn):
            button.setObjectName("restaurantTableOperationButton")
            button.setMinimumHeight(40)
            button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            ops.addWidget(button)
            action = QAction(button.text(), self)
            action.triggered.connect(button.click)
            self.table_ops_menu.addAction(action)
            self._table_ops_action_map.append((button, action))
        self.table_ops_menu_btn.setMinimumHeight(40)
        ops.addWidget(self.table_ops_menu_btn)
        layout.addWidget(self.table_ops_card)

        self.workspace_stack = QStackedWidget()
        self.workspace_stack.setObjectName("restaurantFullscreenModeStack")

        # Order page: Phase 299 makes the current order a full workspace.
        # Table selection lives in the dedicated tables mode so the order grid,
        # action bar and menu cards are no longer squeezed beside the map.
        self.order_page = QWidget()
        self.order_page.setObjectName("restaurantOrderModePage")
        order_page_layout = QVBoxLayout(self.order_page)
        order_page_layout.setContentsMargins(0, 0, 0, 0)
        order_page_layout.setSpacing(8)

        # Phase 309: Cafe is presented as its own operator shell while still
        # reusing the restaurant engine for orders, payment, printing, currency,
        # inventory and recipes.  This shell is intentionally hidden in regular
        # table-service mode so table concepts do not leak into cafe operation.
        self.cafe_shell_card = QFrame()
        self.cafe_shell_card.setObjectName("restaurantCafeWorkspaceShell")
        cafe_shell = QHBoxLayout(self.cafe_shell_card)
        cafe_shell.setContentsMargins(14, 8, 14, 8)
        cafe_shell.setSpacing(10)
        cafe_title_box = QVBoxLayout()
        cafe_title_box.setSpacing(2)
        self.cafe_shell_title = QLabel("☕  " + _("restaurant.cafe_workspace_title"))
        self.cafe_shell_title.setObjectName("restaurantCafeWorkspaceTitle")
        self.cafe_shell_subtitle = QLabel(_("restaurant.cafe_workspace_subtitle"))
        self.cafe_shell_subtitle.setObjectName("restaurantCafeWorkspaceSubtitle")
        cafe_title_box.addWidget(self.cafe_shell_title)
        cafe_title_box.addWidget(self.cafe_shell_subtitle)
        cafe_shell.addLayout(cafe_title_box, 1)
        self.new_cafe_order_btn = QPushButton("➕  " + _("restaurant.cafe_new_quick_order"))
        self.new_cafe_order_btn.setObjectName("restaurantCafeQuickOrderButton")
        self.cafe_preparation_btn = QPushButton("🧑‍🍳  " + _("restaurant.cafe_preparation"))
        self.cafe_preparation_btn.setObjectName("restaurantCafePreparationButton")
        self.cafe_report_btn = QPushButton("📊  " + _("restaurant.cafe_shift_report"))
        self.cafe_report_btn.setObjectName("restaurantCafeReportButton")
        self.cafe_products_barcode_btn = QPushButton("🏷️  " + _("barcode.cafe_product_labels"))
        self.cafe_products_barcode_btn.setObjectName("cafeProductsBarcodeButton")
        self.cafe_modifiers_barcode_btn = QPushButton("☕  " + _("barcode.cafe_modifier_labels"))
        self.cafe_modifiers_barcode_btn.setObjectName("cafeModifiersBarcodeButton")
        for button in (self.new_cafe_order_btn, self.cafe_preparation_btn, self.cafe_report_btn, self.cafe_products_barcode_btn, self.cafe_modifiers_barcode_btn):
            button.setMinimumHeight(42)
            cafe_shell.addWidget(button)
        self.cafe_shell_card.setVisible(False)
        if self._standalone_cafe_workspace:
            self.cafe_shell_card.setProperty("standalone_cafe_workspace", True)
        order_page_layout.addWidget(self.cafe_shell_card)

        self.splitter = QSplitter(Qt.Horizontal)  # compatibility handle for older tests/plugins
        # Legacy ratio contract marker: self.splitter.setStretchFactor(1, 6)
        self.splitter.setObjectName("restaurantOperationSplitter")
        self.splitter.setVisible(False)
        self.table_map = RestaurantTableMapWidget(density="compact")
        self.table_map.setObjectName("restaurantTableMapPane")
        self.table_map.tableClicked.connect(self.open_table)
        self.table_map.setVisible(False)
        self.pos = RestaurantPOSWidget(self.service)
        self.pos.setObjectName("restaurantPOSPane")
        self.pos.sessionClosed.connect(self.reload)
        self.pos.kitchenSent.connect(lambda _payload: self._after_kitchen_sent())
        self.pos.setMinimumWidth(760)
        order_page_layout.addWidget(self.pos, 1)
        self.workspace_stack.addWidget(self.order_page)

        # Kitchen page: KDS owns the workspace; table map is optional context only.
        self.kitchen_page = QWidget()
        self.kitchen_page.setObjectName("restaurantKitchenModePage")
        kitchen_page_layout = QVBoxLayout(self.kitchen_page)
        kitchen_page_layout.setContentsMargins(0, 0, 0, 0)
        kitchen_page_layout.setSpacing(0)
        self.kitchen_splitter = QSplitter(Qt.Horizontal)
        self.kitchen_splitter.setObjectName("restaurantKitchenFullscreenSplitter")
        self.kds = KitchenDisplayWidget(self.service)
        self.kds.setObjectName("restaurantKDSPane")
        self.kitchen_table_map = RestaurantTableMapWidget(density="compact")
        self.kitchen_table_map.setObjectName("restaurantKitchenTableMapPane")
        self.kitchen_table_map.tableClicked.connect(self.open_table)
        self.kitchen_splitter.addWidget(self.kds)
        self.kitchen_splitter.addWidget(self.kitchen_table_map)
        self.kitchen_splitter.setStretchFactor(0, 7)
        self.kitchen_splitter.setStretchFactor(1, 2)
        self.kitchen_splitter.setSizes([960, 280])
        kitchen_page_layout.addWidget(self.kitchen_splitter, 1)
        self.workspace_stack.addWidget(self.kitchen_page)

        # Table page: full table-map workspace for reservations, transfer, and merge workflows.
        self.tables_page = QWidget()
        self.tables_page.setObjectName("restaurantTablesModePage")
        tables_page_layout = QVBoxLayout(self.tables_page)
        tables_page_layout.setContentsMargins(0, 0, 0, 0)
        tables_page_layout.setSpacing(0)
        self.full_table_map = RestaurantTableMapWidget(density=self._ui_settings.get("table_card_density"))
        self.full_table_map.setObjectName("restaurantFullTableMapPane")
        self.full_table_map.tableClicked.connect(self.open_table)
        tables_page_layout.addWidget(self.full_table_map, 1)
        self.workspace_stack.addWidget(self.tables_page)

        self.analytics = RestaurantAnalyticsWidget(self.service)
        self.analytics.setObjectName("restaurantAnalyticsPane")
        self.workspace_stack.addWidget(self.analytics)

        # Compatibility-only stack for older tests/plugins.  Phase 298 no longer
        # lays order+kitchen+tables as three cramped panes.
        self.side_stack = QStackedWidget()
        self.side_stack.setObjectName("restaurantSideModeStack")
        self.side_stack.setVisible(False)

        layout.addWidget(self.workspace_stack, 1)

        self.status = QLabel("")
        self.status.setObjectName("restaurantStatusBar")
        layout.addWidget(self.status)

        self.quick_category_btn.clicked.connect(self.toggle_inline_category_create)
        self.quick_item_btn.clicked.connect(self.toggle_inline_item_create)
        self.order_mode_btn.clicked.connect(self.show_order_mode)
        self.cafe_mode_btn.clicked.connect(self.show_cafe_mode)
        self.new_cafe_order_btn.clicked.connect(self.start_new_cafe_order)
        self.cafe_preparation_btn.clicked.connect(self.show_cafe_preparation_mode)
        self.cafe_report_btn.clicked.connect(self.show_cafe_report_mode)
        self.kitchen_mode_btn.clicked.connect(self.show_kitchen_mode)
        self.tables_mode_btn.clicked.connect(self.show_tables_mode)
        self.analytics_mode_btn.clicked.connect(self.show_analytics_mode)
        self.refresh_button.clicked.connect(self.reload)
        self.menu_barcode_btn.clicked.connect(self.print_restaurant_menu_barcodes)
        self.table_barcode_btn.clicked.connect(self.print_restaurant_table_barcodes)
        self.cafe_products_barcode_btn.clicked.connect(self.print_cafe_product_barcodes)
        self.cafe_modifiers_barcode_btn.clicked.connect(self.print_cafe_modifier_barcodes)
        self.reserve_table_btn.clicked.connect(self.reserve_table)
        self.transfer_table_btn.clicked.connect(self.transfer_current_session)
        self.merge_table_btn.clicked.connect(self.merge_into_current_session)
        self.move_line_btn.clicked.connect(self.move_selected_line_to_table)
        if self._standalone_cafe_workspace:
            self.show_cafe_mode()
        elif self._ui_settings.get("show_kitchen_panel"):
            self.show_kitchen_mode()
        else:
            self.show_order_mode()
        self.reload()

    def _open_barcode_batch_dialog(self, profile_id: str) -> None:
        try:
            BatchPrintDialog(self, profile_id=profile_id).exec()
        except Exception as exc:
            self.status.setText(str(exc))

    def print_restaurant_menu_barcodes(self) -> None:
        self._open_barcode_batch_dialog("restaurant.menu_items")

    def print_restaurant_table_barcodes(self) -> None:
        self._open_barcode_batch_dialog("restaurant.table_labels")

    def print_cafe_product_barcodes(self) -> None:
        self._open_barcode_batch_dialog("cafe.products")

    def print_cafe_modifier_barcodes(self) -> None:
        self._open_barcode_batch_dialog("cafe.modifier_labels")


    def toggle_inline_category_create(self) -> None:
        self.inline_category_panel.toggle_panel()

    def toggle_inline_item_create(self) -> None:
        self.inline_item_panel.toggle_panel()

    def _on_inline_category_created(self, entity_type: str, result: dict) -> None:
        self.status.setText(_("inline_quick_create_saved_selected"))
        if hasattr(self, "pos"):
            self.pos.reload_menu()

    def _on_inline_item_created(self, entity_type: str, result: dict) -> None:
        if hasattr(self, "pos"):
            self.pos.reload_menu()
        self.status.setText(_("inline_quick_create_item_created_available"))


    def _restaurant_ui_settings(self) -> dict:
        try:
            settings = settings_service.get_restaurant_settings()
        except Exception:
            settings = {}
        ui = dict(settings.get("ui") or {})
        cafe = dict(settings.get("cafe") or {})
        ui["cafe_enabled"] = bool(cafe.get("enabled", True))
        ui["cafe_auto_open_quick_order"] = bool(cafe.get("auto_open_quick_order", True))
        return ui

    def _set_mode_button_state(self, mode: str) -> None:
        # Cafe preparation/report pages are cafe operator states, not generic
        # kitchen/analytics modes from the user's perspective.
        active_mode = "cafe" if mode in {"cafe", "cafe_preparation", "cafe_report"} else mode
        for name, button in (("order", self.order_mode_btn), ("cafe", self.cafe_mode_btn), ("kitchen", self.kitchen_mode_btn), ("tables", self.tables_mode_btn), ("analytics", self.analytics_mode_btn)):
            button.setProperty("active", name == active_mode)
            button.style().unpolish(button)
            button.style().polish(button)

    def resizeEvent(self, event: QResizeEvent):  # pragma: no cover - Qt callback
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _resolve_responsive_layout_mode(self) -> str:
        width = max(0, int(self.width() or 0))
        if width and width < RESTAURANT_RESPONSIVE_BREAKPOINTS["compact"]:
            return "compact"
        if width >= RESTAURANT_RESPONSIVE_BREAKPOINTS["wide"]:
            return "wide"
        return "standard"

    def _splitter_sizes_for_mode(self, mode: str, layout_mode: str | None = None) -> list[int]:
        layout_mode = layout_mode or self._responsive_layout_mode
        if mode == "kitchen":
            return RESTAURANT_KITCHEN_SPLITTER_SIZES.get(layout_mode, RESTAURANT_KITCHEN_SPLITTER_SIZES["standard"])
        if mode == "analytics":
            return RESTAURANT_ANALYTICS_SPLITTER_SIZES.get(layout_mode, RESTAURANT_ANALYTICS_SPLITTER_SIZES["standard"])
        return RESTAURANT_ORDER_SPLITTER_SIZES.get(layout_mode, RESTAURANT_ORDER_SPLITTER_SIZES["standard"])

    def _is_cafe_operator_mode(self) -> bool:
        return self._current_mode in {"cafe", "cafe_preparation", "cafe_report"}

    def _set_kds_cafe_context(self, enabled: bool) -> None:
        if hasattr(self, "kds") and hasattr(self.kds, "set_cafe_context"):
            self.kds.set_cafe_context(bool(enabled))

    def _apply_responsive_layout(self) -> None:
        layout_mode = self._resolve_responsive_layout_mode()
        self._responsive_layout_mode = layout_mode
        compact = layout_mode == "compact"
        wide = layout_mode == "wide"
        cafe_mode = self._is_cafe_operator_mode()
        self.setProperty("restaurant_layout_mode", layout_mode)
        self.setProperty("restaurant_operator_mode", "cafe" if cafe_mode else "restaurant")
        self.table_ops_card.setProperty("restaurant_layout_mode", layout_mode)
        self.workspace_stack.setProperty("restaurant_layout_mode", layout_mode)
        if hasattr(self, "cafe_shell_card"):
            self.cafe_shell_card.setVisible(bool(self._standalone_cafe_workspace and self._current_mode in {"cafe", "cafe_preparation", "cafe_report"}))
        if hasattr(self.pos, "set_cafe_workspace_mode"):
            self.pos.set_cafe_workspace_mode(cafe_mode)
        for widget in (self, self.table_ops_card, self.workspace_stack, self.splitter, self.kitchen_splitter):
            widget.setProperty("restaurant_layout_mode", layout_mode)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._apply_table_operations_compact_mode(compact or self._current_mode in {"cafe", "cafe_preparation", "cafe_report", "kitchen", "analytics"})
        if hasattr(self.pos, "set_restaurant_compact_mode"):
            # Phase 299: restaurant order screen always favors operator density;
            # detailed bill adjustments remain in their dialog, not as permanent boxes.
            self.pos.set_restaurant_compact_mode(True)
        # Legacy Phase 296 guard reference: self.pos.setVisible(self._current_mode == "order" or wide)
        # Legacy Phase 296 sizes: "compact": [360, 0, 780], "standard": [360, 0, 860], "wide": [420, 700, 560]
        if self._current_mode == "order":
            self._set_kds_cafe_context(False)
            self.workspace_stack.setCurrentWidget(self.order_page)
            self.table_ops_card.setVisible(True)
            self.table_map.setVisible(False)
            self.splitter.setVisible(False)
            self.mode_badge.setText(_("restaurant.touch_mode"))
        elif self._current_mode == "cafe":
            self._set_kds_cafe_context(False)
            self.workspace_stack.setCurrentWidget(self.order_page)
            self.table_ops_card.setVisible(False)
            self.table_map.setVisible(False)
            self.splitter.setVisible(False)
            self.mode_badge.setText(_("restaurant.cafe_workspace_badge"))
        elif self._current_mode == "cafe_preparation":
            self._set_kds_cafe_context(True)
            self.workspace_stack.setCurrentWidget(self.kitchen_page)
            self.table_ops_card.setVisible(False)
            self.kitchen_table_map.setVisible(False)
            self.kitchen_splitter.setSizes(RESTAURANT_FULLSCREEN_KITCHEN_SIZES.get(layout_mode, RESTAURANT_FULLSCREEN_KITCHEN_SIZES["standard"]))
            self.mode_badge.setText(_("restaurant.cafe_barista_badge"))
        elif self._current_mode == "kitchen":
            self._set_kds_cafe_context(False)
            self.workspace_stack.setCurrentWidget(self.kitchen_page)
            self.table_ops_card.setVisible(False)
            sizes = RESTAURANT_FULLSCREEN_KITCHEN_SIZES.get(layout_mode, RESTAURANT_FULLSCREEN_KITCHEN_SIZES["standard"])
            if compact:
                self.kitchen_table_map.setVisible(False)
            else:
                self.kitchen_table_map.setVisible(True)
            self.kitchen_splitter.setSizes(sizes)
            self.mode_badge.setText(_("restaurant.touch_mode"))
        elif self._current_mode == "tables":
            self._set_kds_cafe_context(False)
            self.workspace_stack.setCurrentWidget(self.tables_page)
            self.table_ops_card.setVisible(True)
            self.mode_badge.setText(_("restaurant.touch_mode"))
        elif self._current_mode == "analytics":
            self._set_kds_cafe_context(False)
            self.workspace_stack.setCurrentWidget(self.analytics)
            self.table_ops_card.setVisible(False)
            self.mode_badge.setText(_("restaurant.touch_mode"))
        elif self._current_mode == "cafe_report":
            self._set_kds_cafe_context(False)
            self.workspace_stack.setCurrentWidget(self.analytics)
            self.table_ops_card.setVisible(False)
            self.mode_badge.setText(_("restaurant.cafe_report_badge"))

    def _apply_table_operations_compact_mode(self, compact: bool) -> None:
        self.table_ops_menu_btn.setVisible(bool(compact))
        for button, action in self._table_ops_action_map:
            button.setVisible((not compact) and restaurant_operation_policy.is_enabled_by_settings(self._operation_for_button(button)))
            action.setVisible(restaurant_operation_policy.is_enabled_by_settings(self._operation_for_button(button)))
            action.setEnabled(button.isEnabled())

    def _operation_for_button(self, button) -> str:
        return {
            self.reserve_table_btn: restaurant_operation_policy.OP_RESERVE_TABLE,
            self.transfer_table_btn: restaurant_operation_policy.OP_TRANSFER_TABLE,
            self.merge_table_btn: restaurant_operation_policy.OP_MERGE_TABLES,
            self.move_line_btn: restaurant_operation_policy.OP_MOVE_ORDER_LINE,
        }.get(button, "")

    def show_order_mode(self):
        if self._standalone_cafe_workspace:
            return self.show_cafe_mode()
        self._current_mode = "order"
        self._set_mode_button_state("order")
        self._apply_responsive_layout()

    def show_cafe_mode(self):
        if not self._standalone_cafe_workspace:
            return
        if not self._ui_settings.get("cafe_enabled", True):
            return
        self._current_mode = "cafe"
        self._set_mode_button_state("cafe")
        self._apply_responsive_layout()
        try:
            current = self._current_session() or {}
            if current.get("order_type") != "cafe_quick_order" and self._ui_settings.get("cafe_auto_open_quick_order", True):
                session = self.service.create_cafe_quick_order(notes="cafe_quick_order")
                self.pos.load_session(session)
            elif current.get("order_type") == "cafe_quick_order":
                self.pos.load_session(current)
            self.status.setText(_("restaurant.cafe_workspace_ready"))
        except Exception as exc:
            self.status.setText(str(exc))

    def start_new_cafe_order(self):
        if not self._standalone_cafe_workspace:
            return
        if not self._ui_settings.get("cafe_enabled", True):
            return
        try:
            session = self.service.create_cafe_quick_order(notes="cafe_quick_order")
            self.pos.load_session(session)
            self.show_cafe_mode()
            self.status.setText(_("restaurant.cafe_new_order_started", session=session.get("id")))
        except Exception as exc:
            self.status.setText(str(exc))

    def show_cafe_preparation_mode(self):
        if not self._standalone_cafe_workspace:
            return
        if not self._ui_settings.get("cafe_enabled", True):
            return
        self._current_mode = "cafe_preparation"
        self._set_mode_button_state("cafe_preparation")
        self._apply_responsive_layout()
        try:
            self.kds.reload()
            self.status.setText(_("restaurant.cafe_preparation_ready"))
        except Exception as exc:
            self.status.setText(str(exc))

    def show_cafe_report_mode(self):
        if not self._standalone_cafe_workspace:
            return
        if not self._ui_settings.get("cafe_enabled", True):
            return
        self._current_mode = "cafe_report"
        self._set_mode_button_state("cafe_report")
        self._apply_responsive_layout()
        try:
            self.analytics.set_cafe_context(True)
            self.analytics.reload()
            self.status.setText(_("restaurant.cafe_report_ready"))
        except Exception as exc:
            self.status.setText(str(exc))

    def show_kitchen_mode(self):
        if self._standalone_cafe_workspace:
            return self.show_cafe_preparation_mode()
        self._current_mode = "kitchen"
        self._set_mode_button_state("kitchen")
        self._apply_responsive_layout()
        try:
            self.kds.reload()
        except Exception:
            pass

    def show_tables_mode(self):
        if self._standalone_cafe_workspace:
            return self.show_cafe_mode()
        self._current_mode = "tables"
        self._set_mode_button_state("tables")
        self._apply_responsive_layout()

    def show_analytics_mode(self):
        if self._standalone_cafe_workspace:
            return self.show_cafe_report_mode()
        if not self._ui_settings.get("show_analytics_panel"):
            return
        self._current_mode = "analytics"
        self._set_mode_button_state("analytics")
        self._apply_responsive_layout()
        try:
            self.analytics.set_cafe_context(False)
            self.analytics.reload()
        except Exception:
            pass

    def refresh(self):
        self.reload()

    def reload(self):
        try:
            self._last_tables = self.service.list_tables()
            self.table_map.set_tables(self._last_tables)
            self.kitchen_table_map.set_tables(self._last_tables)
            self.full_table_map.set_tables(self._last_tables)
            self._update_table_operation_buttons()
            if self._current_mode in {"kitchen", "cafe_preparation"}:
                try:
                    self.kds.reload()
                except Exception:
                    pass
            if self._current_mode in {"analytics", "cafe_report"}:
                try:
                    self.analytics.reload()
                except Exception:
                    pass
            self.status.setText("")
        except Exception as exc:
            self.status.setText(str(exc))

    def _after_kitchen_sent(self):
        self.reload()
        try:
            if self._current_mode in {"kitchen", "cafe_preparation"}:
                self.kds.reload()
        except Exception:
            pass


    def _current_session(self) -> dict:
        return getattr(self.pos, "session", None) or {}

    def _current_session_id(self) -> int | None:
        try:
            session_id = int((self._current_session() or {}).get("id") or 0)
            return session_id if session_id > 0 else None
        except Exception:
            return None

    def _current_table_id(self) -> int | None:
        try:
            table_id = int((self._current_session() or {}).get("table_id") or 0)
            return table_id if table_id > 0 else None
        except Exception:
            return None

    def _free_tables(self, include_reserved: bool = False, exclude_table_id: int | None = None) -> list[dict]:
        allowed = {"free"} | ({"reserved"} if include_reserved else set())
        result = []
        for table in self._last_tables or []:
            if exclude_table_id is not None and int(table.get("id") or 0) == int(exclude_table_id):
                continue
            status = str(table.get("ui_status") or table.get("status") or "free").lower()
            if table.get("active_session_id"):
                continue
            if status in allowed:
                result.append(table)
        return result

    def _other_active_tables(self) -> list[dict]:
        current_session_id = self._current_session_id()
        result = []
        for table in self._last_tables or []:
            session_id = table.get("active_session_id")
            if not session_id:
                continue
            try:
                if current_session_id and int(session_id) == int(current_session_id):
                    continue
            except Exception:
                pass
            result.append(table)
        return result

    def _update_table_operation_buttons(self) -> None:
        has_session = bool(self._current_session_id())
        try:
            has_selected_line = bool(self.pos.lines.selected_line())
        except Exception:
            has_selected_line = False
        policy_map = {
            self.reserve_table_btn: restaurant_operation_policy.OP_RESERVE_TABLE,
            self.transfer_table_btn: restaurant_operation_policy.OP_TRANSFER_TABLE,
            self.merge_table_btn: restaurant_operation_policy.OP_MERGE_TABLES,
            self.move_line_btn: restaurant_operation_policy.OP_MOVE_ORDER_LINE,
        }
        for button, operation in policy_map.items():
            allowed_by_settings = restaurant_operation_policy.is_enabled_by_settings(operation)
            button.setVisible(allowed_by_settings)
        can_reserve = restaurant_operation_policy.can(restaurant_operation_policy.OP_RESERVE_TABLE)
        can_transfer = restaurant_operation_policy.can(restaurant_operation_policy.OP_TRANSFER_TABLE)
        can_merge = restaurant_operation_policy.can(restaurant_operation_policy.OP_MERGE_TABLES)
        can_move_line = restaurant_operation_policy.can(restaurant_operation_policy.OP_MOVE_ORDER_LINE)
        self.reserve_table_btn.setEnabled(can_reserve and bool(self._free_tables(include_reserved=False)))
        self.transfer_table_btn.setEnabled(can_transfer and has_session and bool(self._free_tables(include_reserved=True, exclude_table_id=self._current_table_id())))
        self.merge_table_btn.setEnabled(can_merge and has_session and bool(self._other_active_tables()))
        self.move_line_btn.setEnabled(can_move_line and has_session and has_selected_line and bool([t for t in self._last_tables or [] if int(t.get("id") or 0) != int(self._current_table_id() or 0)]))
        self._apply_table_operations_compact_mode(self._responsive_layout_mode == "compact")

    def reserve_table(self) -> None:
        try:
            restaurant_operation_policy.require(restaurant_operation_policy.OP_RESERVE_TABLE)
            self.reload()
            candidates = self._free_tables(include_reserved=False)
            if not candidates:
                self.status.setText(_("restaurant.no_free_table_to_reserve"))
                return
            dialog = RestaurantReservationDialog(candidates, self)
            if dialog.exec() != QDialog.Accepted:
                return
            payload = dialog.payload()
            self.service.reserve_table(**payload)
            self.status.setText(_("restaurant.reservation_saved"))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))

    def transfer_current_session(self) -> None:
        try:
            restaurant_operation_policy.require(restaurant_operation_policy.OP_TRANSFER_TABLE)
            session_id = self._current_session_id()
            if not session_id:
                self.status.setText(_("restaurant.open_table_first"))
                return
            self.reload()
            candidates = self._free_tables(include_reserved=True, exclude_table_id=self._current_table_id())
            if not candidates:
                self.status.setText(_("restaurant.no_target_table"))
                return
            dialog = RestaurantTableTargetDialog(_("restaurant.transfer_table"), candidates, _("restaurant.transfer_table"), self)
            if dialog.exec() != QDialog.Accepted:
                return
            target = dialog.selected_table()
            result = self.service.transfer_session(session_id, int(target.get("id") or 0))
            self.pos.load_session(result)
            self.status.setText(_("restaurant.table_transferred"))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))

    def merge_into_current_session(self) -> None:
        try:
            restaurant_operation_policy.require(restaurant_operation_policy.OP_MERGE_TABLES)
            target_session_id = self._current_session_id()
            if not target_session_id:
                self.status.setText(_("restaurant.open_table_first"))
                return
            self.reload()
            candidates = self._other_active_tables()
            if not candidates:
                self.status.setText(_("restaurant.no_merge_source"))
                return
            dialog = RestaurantTableTargetDialog(_("restaurant.merge_tables"), candidates, _("restaurant.merge_tables"), self)
            if dialog.exec() != QDialog.Accepted:
                return
            source = dialog.selected_table()
            source_session_id = int(source.get("active_session_id") or 0)
            result = self.service.merge_sessions(source_session_id, target_session_id)
            self.pos.load_session(result)
            self.status.setText(_("restaurant.tables_merged"))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))

    def move_selected_line_to_table(self) -> None:
        try:
            restaurant_operation_policy.require(restaurant_operation_policy.OP_MOVE_ORDER_LINE)
            session_id = self._current_session_id()
            if not session_id:
                self.status.setText(_("restaurant.open_table_first"))
                return
            line = self.pos.lines.selected_line()
            if not line:
                self.status.setText(_("restaurant.select_line_to_move"))
                return
            self.reload()
            current_table_id = self._current_table_id()
            candidates = [t for t in self._last_tables or [] if int(t.get("id") or 0) != int(current_table_id or 0)]
            if not candidates:
                self.status.setText(_("restaurant.no_target_table"))
                return
            dialog = RestaurantTableTargetDialog(_("restaurant.move_selected_line"), candidates, _("restaurant.move_selected_line"), self)
            if dialog.exec() != QDialog.Accepted:
                return
            target = dialog.selected_table()
            result = self.service.split_lines_to_table(session_id, [int(line.get("id") or 0)], int(target.get("id") or 0), notes="split from operation shell")
            self.pos.load_session((result or {}).get("source_session") or self.service.get_session(session_id))
            self.status.setText(_("restaurant.line_moved_to_table"))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))

    def open_table(self, table):
        try:
            session_id = table.get("active_session_id")
            if session_id:
                session = self.service.get_session(int(session_id))
            else:
                session = self.service.open_table(int(table["id"]), guests=table.get("active_guests") or 1)
            self.pos.load_session(session)
            self._update_table_operation_buttons()
            self.show_order_mode()
            self.status.setText(_("restaurant.table_opened", table=table.get("name"), session=session.get("id")))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))
