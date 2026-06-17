# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from core.services.restaurant_service import restaurant_service
from i18n.translator import qt_layout_direction, translate as _
from views.restaurant.table_map_widget import RestaurantTableMapWidget
from views.restaurant.restaurant_pos_widget import RestaurantPOSWidget
from views.restaurant.kitchen_display_widget import KitchenDisplayWidget
from views.restaurant.restaurant_analytics_widget import RestaurantAnalyticsWidget


class RestaurantDashboard(QWidget):
    """Touch-friendly restaurant dashboard.

    Left side: table map. Right side: active session order lines and kitchen
    actions. It remains a thin UI wrapper over RestaurantService.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = restaurant_service
        self.setObjectName("restaurantDashboard")
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_card = QFrame()
        header_card.setObjectName("restaurantHeaderCard")
        header = QHBoxLayout(header_card)
        header.setContentsMargins(18, 14, 18, 14)
        title = QLabel("🍽  " + _("restaurant.dashboard"))
        title.setObjectName("restaurantDashboardTitle")
        header.addWidget(title)
        header.addStretch()
        self.mode_badge = QLabel(_("restaurant.touch_mode"))
        self.mode_badge.setObjectName("restaurantModeBadge")
        header.addWidget(self.mode_badge)
        self.refresh_button = QPushButton("↻  " + _("common.refresh"))
        self.refresh_button.setObjectName("restaurantRefreshButton")
        self.refresh_button.setMinimumHeight(54)
        self.refresh_button.clicked.connect(self.reload)
        header.addWidget(self.refresh_button)
        layout.addWidget(header_card)

        splitter = QSplitter(Qt.Horizontal)
        self.table_map = RestaurantTableMapWidget()
        self.table_map.setObjectName("restaurantTableMapPane")
        self.table_map.tableClicked.connect(self.open_table)
        splitter.addWidget(self.table_map)

        self.pos = RestaurantPOSWidget(self.service)
        self.pos.setObjectName("restaurantPOSPane")
        self.pos.sessionClosed.connect(self.reload)
        self.pos.kitchenSent.connect(lambda _payload: self._after_kitchen_sent())
        splitter.addWidget(self.pos)

        self.kds = KitchenDisplayWidget(self.service)
        self.kds.setObjectName("restaurantKDSPane")
        splitter.addWidget(self.kds)

        self.analytics = RestaurantAnalyticsWidget(self.service)
        self.analytics.setObjectName("restaurantAnalyticsPane")
        splitter.addWidget(self.analytics)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        splitter.setStretchFactor(3, 1)
        layout.addWidget(splitter)

        self.status = QLabel("")
        self.status.setObjectName("restaurantStatusBar")
        layout.addWidget(self.status)
        self.reload()

    def refresh(self):
        self.reload()

    def reload(self):
        try:
            self.table_map.set_tables(self.service.list_tables())
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
            self.kds.reload()
            self.analytics.reload()
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
            self.status.setText(_("restaurant.table_opened", table=table.get("name"), session=session.get("id")))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))
