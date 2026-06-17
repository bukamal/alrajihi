# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from i18n.translator import qt_layout_direction, translate as _


class KitchenDisplayWidget(QWidget):
    """Touch-friendly kitchen display screen (KDS).

    The widget is deliberately thin: it reads KOT tickets from RestaurantService
    and sends status transitions back through the service/gateway boundary.
    """

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_ticket = None
        self.setObjectName("restaurantKitchenDisplay")
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.title = QLabel("👨‍🍳  " + _("restaurant.kds.title"))
        self.title.setObjectName("restaurantKDSTitle")
        header.addWidget(self.title)
        header.addStretch()
        self.station_filter = QComboBox()
        self.station_filter.setObjectName("restaurantKDSStationFilter")
        self.station_filter.setMinimumHeight(50)
        self.station_filter.currentIndexChanged.connect(self.reload)
        header.addWidget(self.station_filter)
        self.refresh_btn = QPushButton("↻  " + _("common.refresh"))
        self.refresh_btn.setObjectName("restaurantKDSRefreshButton")
        self.refresh_btn.setMinimumHeight(50)
        self.refresh_btn.clicked.connect(self.reload)
        header.addWidget(self.refresh_btn)
        root.addLayout(header)

        body = QHBoxLayout()
        self.tickets = QListWidget()
        self.tickets.setObjectName("restaurantKDSTickets")
        self.tickets.setMinimumWidth(260)
        self.tickets.itemSelectionChanged.connect(self._ticket_selected)
        body.addWidget(self.tickets, 1)

        detail_card = QFrame()
        detail_card.setObjectName("restaurantKDSDetailCard")
        detail = QVBoxLayout(detail_card)
        self.detail_title = QLabel(_("restaurant.kds.no_ticket"))
        self.detail_title.setObjectName("restaurantKDSDetailTitle")
        detail.addWidget(self.detail_title)
        self.lines = QListWidget()
        self.lines.setObjectName("restaurantKDSLines")
        detail.addWidget(self.lines, 1)
        actions = QHBoxLayout()
        self.preparing_btn = QPushButton("🔥  " + _("restaurant.kds.preparing"))
        self.ready_btn = QPushButton("✅  " + _("restaurant.kds.ready"))
        self.served_btn = QPushButton("🍽  " + _("restaurant.kds.served"))
        for button in (self.preparing_btn, self.ready_btn, self.served_btn):
            button.setMinimumHeight(58)
            actions.addWidget(button)
        self.preparing_btn.clicked.connect(lambda: self._set_ticket_status("preparing"))
        self.ready_btn.clicked.connect(lambda: self._set_ticket_status("ready"))
        self.served_btn.clicked.connect(lambda: self._set_ticket_status("served"))
        detail.addLayout(actions)
        body.addWidget(detail_card, 2)
        root.addLayout(body, 1)

        self.status = QLabel("")
        self.status.setObjectName("restaurantKDSStatus")
        root.addWidget(self.status)
        self._set_actions_enabled(False)
        self._load_stations()
        self.reload()

    def _set_actions_enabled(self, enabled: bool):
        for button in (self.preparing_btn, self.ready_btn, self.served_btn):
            button.setEnabled(bool(enabled))

    def _load_stations(self):
        self.station_filter.blockSignals(True)
        self.station_filter.clear()
        self.station_filter.addItem(_("restaurant.kds.all_stations"), None)
        try:
            for station in self.service.list_kitchen_stations():
                self.station_filter.addItem(station.get("name") or station.get("code") or str(station.get("id")), station.get("id"))
        except Exception:
            pass
        self.station_filter.blockSignals(False)

    def reload(self):
        self.tickets.clear()
        try:
            station_id = self.station_filter.currentData() if hasattr(self, "station_filter") else None
            tickets = self.service.list_kitchen_tickets(status="all", limit=80, station_id=station_id)
            for ticket in tickets:
                item = QListWidgetItem(self._ticket_label(ticket))
                item.setData(256, ticket)
                self.tickets.addItem(item)
            self.status.setText(_("restaurant.kds.loaded"))
        except Exception as exc:
            self.status.setText(str(exc))
        self._set_actions_enabled(False)

    def _ticket_label(self, ticket: dict) -> str:
        status = ticket.get("status") or "sent"
        station = ticket.get('station_name') or _("restaurant.kds.all_stations")
        return f"#{ticket.get('id')}  {ticket.get('table_name') or ticket.get('table_id') or ''} — {station}\n{_(f'restaurant.kds.status.{status}')} — {ticket.get('line_count') or 0}"

    def _ticket_selected(self):
        items = self.tickets.selectedItems()
        if not items:
            self.current_ticket = None
            self.detail_title.setText(_("restaurant.kds.no_ticket"))
            self.lines.clear()
            self._set_actions_enabled(False)
            return
        ticket = items[0].data(256) or {}
        try:
            self.current_ticket = self.service.get_kitchen_ticket(int(ticket["id"]))
            self._render_ticket(self.current_ticket)
        except Exception as exc:
            self.status.setText(str(exc))
            self._set_actions_enabled(False)

    def _render_ticket(self, ticket: dict):
        status = ticket.get("status") or "sent"
        self.detail_title.setText(f"#{ticket.get('id')} — {ticket.get('table_name') or ticket.get('table_id')} — {_(f'restaurant.kds.status.{status}')}" )
        self.lines.clear()
        for line in ticket.get("lines") or []:
            label = f"{line.get('quantity') or '1'} × {line.get('item_name') or ''}"
            if line.get("notes"):
                label += f"\n📝 {line.get('notes')}"
            item = QListWidgetItem(label)
            self.lines.addItem(item)
        self._set_actions_enabled(True)

    def _set_ticket_status(self, status: str):
        if not self.current_ticket:
            return
        try:
            self.current_ticket = self.service.update_kitchen_ticket_status(int(self.current_ticket["id"]), status)
            self._render_ticket(self.current_ticket)
            self.status.setText(_("restaurant.kds.updated"))
            self.reload()
        except Exception as exc:
            self.status.setText(str(exc))
