# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QGridLayout, QWidget

from i18n.translator import translate as _


class RestaurantTableMapWidget(QWidget):
    tableClicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("restaurantTableMap")
        self._layout = QGridLayout(self)
        self._layout.setSpacing(18)
        self._layout.setContentsMargins(18, 18, 18, 18)
        self._tables = []

    def set_tables(self, tables):
        self._tables = list(tables or [])
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not self._tables:
            for index in range(1, 13):
                table = {"id": index, "name": f"{_( 'restaurant.table' )} {index}", "status": "free", "seats": 4}
                button = self._button(table)
                self._layout.addWidget(button, (index - 1) // 4, (index - 1) % 4)
            return
        for index, table in enumerate(self._tables):
            self._layout.addWidget(self._button(table), index // 4, index % 4)

    def _button(self, table):
        button = QPushButton(self._label(table))
        button.setObjectName("restaurantTableButton")
        button.setMinimumSize(178, 128)
        button.setCursor(Qt.PointingHandCursor)
        button.setProperty("restaurant_status", self._ui_status(table))
        button.clicked.connect(lambda _=False, t=table: self.tableClicked.emit(t))
        return button

    def _ui_status(self, table):
        status = table.get("status") or "free"
        if status == "occupied" and table.get("active_session_id"):
            return "occupied"
        return status

    def _label(self, table):
        status = table.get("status") or "free"
        status_label = _("restaurant.status." + status) if status else ""
        guests = table.get("active_guests") or ""
        seats = table.get("seats") or ""
        icon = {"free": "🟢", "occupied": "🍽", "reserved": "📌", "payment": "💳"}.get(status, "🍽")
        table_name = str(table.get("name") or table.get("id"))
        lines = [f"{icon}  {table_name}", status_label]
        if guests:
            lines.append(_("restaurant.guests_count", guests=guests))
        elif seats:
            lines.append(_("restaurant.seats_count", seats=seats))
        return "\n".join(lines)
