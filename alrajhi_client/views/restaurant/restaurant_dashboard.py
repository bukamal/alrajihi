# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QStackedWidget,
    QVBoxLayout, QWidget
)

from core.services.restaurant_service import restaurant_service
from core.services.settings_service import settings_service
from i18n.translator import qt_layout_direction, translate as _
from views.restaurant.table_map_widget import RestaurantTableMapWidget
from views.restaurant.restaurant_pos_widget import RestaurantPOSWidget
from views.restaurant.kitchen_display_widget import KitchenDisplayWidget
from views.restaurant.restaurant_analytics_widget import RestaurantAnalyticsWidget
from workspace.operational.operational_shell_contract import bind_operational_shell


class RestaurantDashboard(QWidget):
    """Unified Restaurant Operation Shell.

    Phase 283: the operational screen is centered around the live order.  The
    default view is two-pane (tables + current order/menu).  Kitchen display and
    analytics are explicit modes instead of permanent crowded panes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        bind_operational_shell(self, 'restaurant')
        self.service = restaurant_service
        self._ui_settings = self._restaurant_ui_settings()
        self.setObjectName("restaurantDashboard")
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_card = QFrame()
        header_card.setObjectName("restaurantHeaderCard")
        header = QHBoxLayout(header_card)
        header.setContentsMargins(16, 10, 16, 10)
        title = QLabel("🍽  " + _("restaurant.operation_shell"))
        title.setObjectName("restaurantDashboardTitle")
        header.addWidget(title)
        header.addStretch()

        self.order_mode_btn = QPushButton("🧾  " + _("restaurant.mode.order"))
        self.order_mode_btn.setObjectName("restaurantOrderModeButton")
        self.kitchen_mode_btn = QPushButton("👨‍🍳  " + _("restaurant.mode.kitchen"))
        self.kitchen_mode_btn.setObjectName("restaurantKitchenModeButton")
        self.analytics_mode_btn = QPushButton("📊  " + _("restaurant.mode.analytics"))
        self.analytics_mode_btn.setObjectName("restaurantAnalyticsModeButton")
        self.mode_badge = QLabel(_("restaurant.touch_mode"))
        self.mode_badge.setObjectName("restaurantModeBadge")
        self.refresh_button = QPushButton("↻  " + _("common.refresh"))
        self.refresh_button.setObjectName("restaurantRefreshButton")
        for button in (self.order_mode_btn, self.kitchen_mode_btn, self.analytics_mode_btn, self.refresh_button):
            button.setMinimumHeight(44)
        self.analytics_mode_btn.setVisible(bool(self._ui_settings.get("show_analytics_panel")))
        header.addWidget(self.order_mode_btn)
        header.addWidget(self.kitchen_mode_btn)
        header.addWidget(self.analytics_mode_btn)
        header.addWidget(self.mode_badge)
        header.addWidget(self.refresh_button)
        layout.addWidget(header_card)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("restaurantOperationSplitter")
        self.table_map = RestaurantTableMapWidget(density=self._ui_settings.get("table_card_density"))
        self.table_map.setObjectName("restaurantTableMapPane")
        self.table_map.tableClicked.connect(self.open_table)
        self.splitter.addWidget(self.table_map)

        self.pos = RestaurantPOSWidget(self.service)
        self.pos.setObjectName("restaurantPOSPane")
        self.pos.sessionClosed.connect(self.reload)
        self.pos.kitchenSent.connect(lambda _payload: self._after_kitchen_sent())
        self.splitter.addWidget(self.pos)

        self.side_stack = QStackedWidget()
        self.side_stack.setObjectName("restaurantSideModeStack")
        self.kds = KitchenDisplayWidget(self.service)
        self.kds.setObjectName("restaurantKDSPane")
        self.analytics = RestaurantAnalyticsWidget(self.service)
        self.analytics.setObjectName("restaurantAnalyticsPane")
        self.side_stack.addWidget(self.kds)
        self.side_stack.addWidget(self.analytics)
        self.splitter.addWidget(self.side_stack)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 6)
        self.splitter.setStretchFactor(2, 3)
        self.splitter.setSizes([360, 760, 0])
        layout.addWidget(self.splitter, 1)

        self.status = QLabel("")
        self.status.setObjectName("restaurantStatusBar")
        layout.addWidget(self.status)

        self.order_mode_btn.clicked.connect(self.show_order_mode)
        self.kitchen_mode_btn.clicked.connect(self.show_kitchen_mode)
        self.analytics_mode_btn.clicked.connect(self.show_analytics_mode)
        self.refresh_button.clicked.connect(self.reload)
        if self._ui_settings.get("show_kitchen_panel"):
            self.show_kitchen_mode()
        else:
            self.show_order_mode()
        self.reload()

    def _restaurant_ui_settings(self) -> dict:
        try:
            settings = settings_service.get_restaurant_settings()
        except Exception:
            settings = {}
        return dict(settings.get("ui") or {})

    def _set_mode_button_state(self, mode: str) -> None:
        for name, button in (("order", self.order_mode_btn), ("kitchen", self.kitchen_mode_btn), ("analytics", self.analytics_mode_btn)):
            button.setProperty("active", name == mode)
            button.style().unpolish(button)
            button.style().polish(button)

    def show_order_mode(self):
        self.side_stack.setVisible(False)
        self.splitter.setSizes([390, 850, 0])
        self._set_mode_button_state("order")

    def show_kitchen_mode(self):
        self.side_stack.setCurrentWidget(self.kds)
        self.side_stack.setVisible(True)
        self.splitter.setSizes([330, 650, 360])
        self._set_mode_button_state("kitchen")
        try:
            self.kds.reload()
        except Exception:
            pass

    def show_analytics_mode(self):
        if not self._ui_settings.get("show_analytics_panel"):
            return
        self.side_stack.setCurrentWidget(self.analytics)
        self.side_stack.setVisible(True)
        self.splitter.setSizes([330, 650, 300])
        self._set_mode_button_state("analytics")
        try:
            self.analytics.reload()
        except Exception:
            pass

    def refresh(self):
        self.reload()

    def reload(self):
        try:
            self.table_map.set_tables(self.service.list_tables())
            if self.side_stack.isVisible() and self.side_stack.currentWidget() is self.kds:
                try:
                    self.kds.reload()
                except Exception:
                    pass
            if self.side_stack.isVisible() and self.side_stack.currentWidget() is self.analytics:
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
            if self.side_stack.isVisible() and self.side_stack.currentWidget() is self.kds:
                self.kds.reload()
        except Exception:
            pass

    def open_table(self, table):
        try:
            session_id = table.get("active_session_id")
            if session_id:
                session = self.service.get_session(int(session_id))
            else:
                session = self.service.open_table(int(table["id"]), guests=table.get("active_guests") or 1)
            self.pos.load_session(session)
            self.show_order_mode()
            self.status.setText(_("restaurant.table_opened", table=table.get("name"), session=session.get("id")))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))
