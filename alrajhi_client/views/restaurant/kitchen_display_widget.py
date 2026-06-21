# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from i18n.translator import qt_layout_direction, translate as _


class KitchenDisplayWidget(QWidget):
    """Touch-friendly kitchen display screen (KDS).

    Phase 288 hardens this into an operational board rather than a raw ticket
    list: station/status filters, active counters, overdue markers, and explicit
    status transitions for preparing/ready/served.
    """

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_ticket = None
        self._last_tickets: list[dict] = []
        self._cafe_context = False
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

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("restaurantKDSStatusFilter")
        self.status_filter.setMinimumHeight(50)
        self.status_filter.addItem(_("restaurant.kds.filter.active"), "active")
        self.status_filter.addItem(_("restaurant.kds.status.sent"), "sent")
        self.status_filter.addItem(_("restaurant.kds.status.preparing"), "preparing")
        self.status_filter.addItem(_("restaurant.kds.status.ready"), "ready")
        self.status_filter.addItem(_("restaurant.kds.status.served"), "served")
        self.status_filter.addItem(_("restaurant.kds.status.cancelled"), "cancelled")
        self.status_filter.addItem(_("restaurant.kds.filter.all"), "all")
        self.status_filter.currentIndexChanged.connect(self.reload)
        header.addWidget(self.status_filter)

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

        self.counter_bar = QHBoxLayout()
        self.counter_bar.setObjectName("restaurantKDSCounterBar")
        self.counter_labels = {}
        for key in ("sent", "preparing", "ready", "overdue"):
            label = QLabel()
            label.setObjectName(f"restaurantKDSCounter_{key}")
            self.counter_labels[key] = label
            self.counter_bar.addWidget(label)
        self.counter_bar.addStretch()
        root.addLayout(self.counter_bar)

        body_frame = QFrame()
        body_frame.setObjectName("restaurantKDSBoardBody")
        body = QHBoxLayout(body_frame)
        body.setContentsMargins(10, 10, 10, 10)
        body.setSpacing(12)
        self.tickets = QListWidget()
        self.tickets.setObjectName("restaurantKDSTickets")
        self.tickets.setMinimumWidth(320)
        self.tickets.itemSelectionChanged.connect(self._ticket_selected)
        body.addWidget(self.tickets, 1)

        detail_card = QFrame()
        detail_card.setObjectName("restaurantKDSDetailCard")
        detail = QVBoxLayout(detail_card)
        self.detail_title = QLabel(_("restaurant.kds.no_ticket"))
        self.detail_title.setObjectName("restaurantKDSDetailTitle")
        detail.addWidget(self.detail_title)
        self.detail_meta = QLabel("")
        self.detail_meta.setObjectName("restaurantKDSDetailMeta")
        detail.addWidget(self.detail_meta)
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
        root.addWidget(body_frame, 1)

        self.status = QLabel("")
        self.status.setObjectName("restaurantKDSStatus")
        root.addWidget(self.status)
        self._set_actions_enabled(False)
        self._load_stations()
        self.reload()

    def set_cafe_context(self, enabled: bool) -> None:
        self._cafe_context = bool(enabled)
        self.setProperty("restaurant_kds_context", "cafe" if self._cafe_context else "restaurant")
        self.title.setText(("☕  " + _("restaurant.cafe_preparation_board")) if self._cafe_context else ("👨‍🍳  " + _("restaurant.kds.title")))
        self.preparing_btn.setText(("🔥  " + _("restaurant.cafe_preparing")) if self._cafe_context else ("🔥  " + _("restaurant.kds.preparing")))
        self.ready_btn.setText(("✅  " + _("restaurant.cafe_ready")) if self._cafe_context else ("✅  " + _("restaurant.kds.ready")))
        self.served_btn.setText(("📦  " + _("restaurant.cafe_delivered")) if self._cafe_context else ("🍽  " + _("restaurant.kds.served")))
        for widget in (self, self.title, self.preparing_btn, self.ready_btn, self.served_btn):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _ticket_context_label(self, ticket: dict) -> str:
        table = ticket.get("table_name") or ticket.get("table_id") or ""
        if self._cafe_context and str(table).strip().lower() == "cafe":
            return _("restaurant.cafe_order_label")
        return str(table or "")

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
            status = self.status_filter.currentData() if hasattr(self, "status_filter") else "active"
            order_type = "cafe_quick_order" if getattr(self, "_cafe_context", False) else None
            tickets = self.service.list_kitchen_tickets(status=status or "active", limit=120, station_id=station_id, order_type=order_type)
            self._last_tickets = list(tickets or [])
            for ticket in self._last_tickets:
                item = QListWidgetItem(self._ticket_label(ticket))
                item.setData(256, ticket)
                self.tickets.addItem(item)
            self._render_counters(self._last_tickets)
            self.status.setText(_("restaurant.kds.loaded"))
        except Exception as exc:
            self.status.setText(str(exc))
        self._set_actions_enabled(False)

    def _render_counters(self, tickets: list[dict]):
        counts = {"sent": 0, "preparing": 0, "ready": 0, "overdue": 0}
        for ticket in tickets or []:
            status = str(ticket.get("status") or "sent")
            if status in counts:
                counts[status] += 1
            if ticket.get("is_overdue"):
                counts["overdue"] += 1
        self.counter_labels["sent"].setText(f"📨 {_('restaurant.kds.status.sent')}: {counts['sent']}")
        self.counter_labels["preparing"].setText(f"🔥 {_('restaurant.kds.status.preparing')}: {counts['preparing']}")
        self.counter_labels["ready"].setText(f"✅ {_('restaurant.kds.status.ready')}: {counts['ready']}")
        self.counter_labels["overdue"].setText(f"⏱ {_('restaurant.kds.overdue')}: {counts['overdue']}")

    def _status_icon(self, status: str) -> str:
        return {
            "sent": "📨",
            "preparing": "🔥",
            "ready": "✅",
            "served": "🍽",
            "cancelled": "🚫",
        }.get(str(status or "sent"), "📨")

    def _ticket_label(self, ticket: dict) -> str:
        status = ticket.get("status") or "sent"
        station = ticket.get('station_name') or _("restaurant.kds.all_stations")
        elapsed = ticket.get("elapsed_minutes") or 0
        overdue = "  ⚠ " + _("restaurant.kds.overdue") if ticket.get("is_overdue") else ""
        table = self._ticket_context_label(ticket)
        status_label = _(f"restaurant.kds.status.{status}")
        lines_label = _("restaurant.lines_count")
        minutes_label = _("restaurant.kds.minutes")
        line_count = ticket.get('line_count') or 0
        ticket_id = ticket.get('id')
        return (
            f"{self._status_icon(status)}  {status_label} — {table}{overdue}\n"
            f"#{ticket_id}  |  {station}  |  {line_count} {lines_label}  |  {elapsed} {minutes_label}"
        )

    def _ticket_selected(self):
        items = self.tickets.selectedItems()
        if not items:
            self.current_ticket = None
            self.detail_title.setText(_("restaurant.kds.no_ticket"))
            self.detail_meta.setText("")
            self.lines.clear()
            self._set_actions_enabled(False)
            return
        ticket = items[0].data(256) or {}
        try:
            self.current_ticket = self.service.get_kitchen_ticket(int(ticket["id"]))
            # Preserve computed list metadata when detail endpoint does not include it.
            self.current_ticket.update({k: ticket.get(k) for k in ("elapsed_minutes", "is_overdue", "priority") if k in ticket})
            self._render_ticket(self.current_ticket)
        except Exception as exc:
            self.status.setText(str(exc))
            self._set_actions_enabled(False)

    def _render_ticket(self, ticket: dict):
        status = ticket.get("status") or "sent"
        self.detail_title.setText(f"{self._status_icon(status)}  {_(f'restaurant.kds.status.{status}')} — {self._ticket_context_label(ticket)} — #{ticket.get('id')}")
        station = ticket.get("station_name") or _("restaurant.kds.all_stations")
        elapsed = ticket.get("elapsed_minutes") or 0
        overdue = " — " + _("restaurant.kds.overdue") if ticket.get("is_overdue") else ""
        self.detail_meta.setText(f"{station} — {elapsed} {_('restaurant.kds.minutes')}{overdue}")
        self.lines.clear()
        for line in ticket.get("lines") or []:
            label = f"{line.get('quantity') or '1'} × {line.get('item_name') or ''}"
            if line.get("notes"):
                label += f"\n📝 {line.get('notes')}"
            item = QListWidgetItem(label)
            self.lines.addItem(item)
        self._set_actions_enabled(status not in {"served", "cancelled"})

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
