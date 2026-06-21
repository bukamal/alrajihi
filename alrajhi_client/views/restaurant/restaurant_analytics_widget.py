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
        self._cafe_context = False
        self.labels: dict[str, QLabel] = {}
        for idx, key in enumerate(("open_sessions", "payments_total", "cash_total", "card_total", "top_item", "kitchen_tickets", "unpaid_open_balance", "shift_close_status")):
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
            self.cards.addWidget(card, idx // 4, idx % 4)

        self.status = QLabel("")
        self.status.setObjectName("restaurantAnalyticsStatus")
        layout.addWidget(self.status)
        self.reload()

    def set_cafe_context(self, enabled: bool) -> None:
        self._cafe_context = bool(enabled)
        self.setProperty("restaurant_analytics_context", "cafe" if self._cafe_context else "restaurant")
        self.title.setText(("☕  " + _("restaurant.cafe_shift_report_title")) if self._cafe_context else ("📊  " + _("restaurant.analytics")))
        for widget in (self, self.title):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.reload()

    def reload(self) -> None:
        try:
            if getattr(self, "_cafe_context", False):
                payload: dict[str, Any] = self.service.cafe_shift_report()
                summary = payload.get("summary") or {}
                controls = payload.get("operational_controls") or {}
                self.labels["open_sessions"].setText(str(summary.get("open_orders", 0)))
                self.labels["payments_total"].setText(str(summary.get("payments_total", "0")))
                self.labels["cash_total"].setText(str(summary.get("cash_total", "0")))
                self.labels["card_total"].setText(str(summary.get("card_total", "0")))
                top_drinks = payload.get("top_drinks") or []
                self.labels["top_item"].setText(str((top_drinks[0] if top_drinks else {}).get("item_name", "—")))
                self.labels["kitchen_tickets"].setText(str(controls.get("active_barista_tickets", 0)))
                self.labels["unpaid_open_balance"].setText(str(summary.get("unpaid_open_balance", "0")))
                self.labels["shift_close_status"].setText(_("restaurant.shift.can_close") if controls.get("can_close_shift") else _("restaurant.shift.blocked"))
                top_modifiers = payload.get("top_modifiers") or []
                low_stock = payload.get("low_stock_alerts") or []
                top_modifier_label = _("restaurant.cafe_top_modifier")
                low_stock_label = _("restaurant.cafe_low_stock_alerts")
                top_modifier_name = (top_modifiers[0] if top_modifiers else {}).get("name") or "—"
                self.status.setText(f"{top_modifier_label}: {top_modifier_name} — {low_stock_label}: {len(low_stock)}")
                return
            payload: dict[str, Any] = self.service.restaurant_analytics()
            summary = payload.get("summary") or {}
            self.labels["open_sessions"].setText(str(summary.get("open_sessions", 0)))
            self.labels["payments_total"].setText(str(summary.get("payments_total", "0")))
            top_items = payload.get("top_items") or []
            self.labels["top_item"].setText(str((top_items[0] if top_items else {}).get("item_name", "—")))
            kitchen = payload.get("kitchen_performance") or []
            tickets = sum(int(row.get("tickets") or 0) for row in kitchen)
            self.labels["kitchen_tickets"].setText(str(tickets))
            try:
                shift = self.service.restaurant_shift_report()
                shift_summary = shift.get("summary") or {}
                controls = shift.get("operational_controls") or {}
                self.labels["cash_total"].setText(str(shift_summary.get("cash_total", "0")))
                self.labels["card_total"].setText(str(shift_summary.get("card_total", "0")))
                self.labels["unpaid_open_balance"].setText(str(shift_summary.get("unpaid_open_balance", "0")))
                self.labels["shift_close_status"].setText(_("restaurant.shift.can_close") if controls.get("can_close_shift") else _("restaurant.shift.blocked"))
            except Exception:
                self.labels["cash_total"].setText("—")
                self.labels["card_total"].setText("—")
                self.labels["unpaid_open_balance"].setText("—")
                self.labels["shift_close_status"].setText("—")
            self.status.setText("")
        except Exception as exc:
            self.status.setText(str(exc))
