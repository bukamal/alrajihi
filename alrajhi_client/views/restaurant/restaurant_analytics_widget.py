# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from i18n.translator import translate as _


class RestaurantAnalyticsWidget(QWidget):
    """Touch-friendly read-only restaurant KPI panel."""

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("restaurantAnalyticsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QFrame()
        header.setObjectName("restaurantAnalyticsHeader")
        header_layout = QGridLayout(header)
        self.title = QLabel("📊  " + _("restaurant.analytics"))
        self.title.setObjectName("restaurantAnalyticsTitle")
        header_layout.addWidget(self.title, 0, 0)
        self.refresh_button = QPushButton("↻  " + _("common.refresh"))
        self.refresh_button.setObjectName("restaurantAnalyticsRefresh")
        self.refresh_button.setMinimumHeight(44)
        self.refresh_button.clicked.connect(self.reload)
        header_layout.addWidget(self.refresh_button, 0, 1)
        layout.addWidget(header)

        self.cards = QGridLayout()
        self.cards.setSpacing(8)
        layout.addLayout(self.cards)
        self.labels: dict[str, QLabel] = {}
        for idx, key in enumerate(("open_sessions", "payments_total", "top_item", "kitchen_tickets")):
            card = QFrame()
            card.setObjectName("restaurantAnalyticsCard")
            card_layout = QVBoxLayout(card)
            caption = QLabel(_("restaurant.analytics." + key))
            caption.setObjectName("restaurantAnalyticsCaption")
            value = QLabel("—")
            value.setObjectName("restaurantAnalyticsValue")
            card_layout.addWidget(caption)
            card_layout.addWidget(value)
            self.labels[key] = value
            self.cards.addWidget(card, idx // 2, idx % 2)

        self.status = QLabel("")
        self.status.setObjectName("restaurantAnalyticsStatus")
        layout.addWidget(self.status)
        self.reload()

    def reload(self) -> None:
        try:
            payload: dict[str, Any] = self.service.restaurant_analytics()
            summary = payload.get("summary") or {}
            self.labels["open_sessions"].setText(str(summary.get("open_sessions", 0)))
            self.labels["payments_total"].setText(str(summary.get("payments_total", "0")))
            top_items = payload.get("top_items") or []
            self.labels["top_item"].setText(str((top_items[0] if top_items else {}).get("item_name", "—")))
            kitchen = payload.get("kitchen_performance") or []
            tickets = sum(int(row.get("tickets") or 0) for row in kitchen)
            self.labels["kitchen_tickets"].setText(str(tickets))
            self.status.setText("")
        except Exception as exc:
            self.status.setText(str(exc))
