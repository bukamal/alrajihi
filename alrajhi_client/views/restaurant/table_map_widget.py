# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QGridLayout, QWidget

from currency import currency
from i18n.translator import translate as _


def _money(value) -> str:
    try:
        return currency.format_display_amount(currency.to_display(Decimal(str(value or "0"))))
    except (InvalidOperation, TypeError, ValueError):
        return str(value or "0")


class RestaurantTableMapWidget(QWidget):
    tableClicked = pyqtSignal(dict)

    def __init__(self, parent=None, density=None):
        super().__init__(parent)
        self.setObjectName("restaurantTableMap")
        self._density = (density or "touch").lower()
        self._layout = QGridLayout(self)
        self._layout.setSpacing(14 if self._density == "compact" else 18)
        self._layout.setContentsMargins(14, 14, 14, 14)
        self._tables = []

    def set_density(self, density: str | None):
        self._density = (density or "touch").lower()
        self.set_tables(self._tables)

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
                self._layout.addWidget(button, (index - 1) // self._columns(), (index - 1) % self._columns())
            return
        for index, table in enumerate(self._tables):
            self._layout.addWidget(self._button(table), index // self._columns(), index % self._columns())

    def _columns(self) -> int:
        return 3 if self._density == "compact" else 4

    def _button(self, table):
        button = QPushButton(self._label(table))
        button.setObjectName("restaurantTableButton")
        button.setMinimumSize(178, 128)
        button.setCursor(Qt.PointingHandCursor)
        button.setProperty("restaurant_status", self._ui_status(table))
        button.clicked.connect(lambda _=False, t=table: self.tableClicked.emit(t))
        return button

    def _ui_status(self, table):
        status = str(table.get("status") or "free").lower()
        kitchen_status = str(table.get("kitchen_status") or table.get("active_kitchen_status") or "").lower()
        if status == "occupied" and kitchen_status in {"sent", "preparing", "waiting_kitchen"}:
            return "kitchen"
        if status == "occupied" and kitchen_status in {"ready", "served"}:
            return "ready"
        if status == "occupied" and table.get("payment_pending"):
            return "payment"
        if status == "occupied" and table.get("active_session_id"):
            return "occupied"
        return status if status in {"free", "occupied", "reserved", "payment"} else "occupied"

    def _status_label(self, ui_status: str) -> str:
        key = f"restaurant.status.{ui_status}"
        translated = _(key)
        return translated if translated != key else _(f"restaurant.status.{ui_status}")

    def _label(self, table):
        ui_status = self._ui_status(table)
        status_label = self._status_label(ui_status)
        guests = table.get("active_guests") or table.get("guests") or ""
        seats = table.get("seats") or ""
        total = table.get("active_total") or table.get("total") or table.get("balance_total")
        elapsed = table.get("elapsed_minutes") or table.get("age_minutes")
        icon = {
            "free": "🟢",
            "occupied": "🍽",
            "kitchen": "👨‍🍳",
            "ready": "✅",
            "reserved": "📌",
            "payment": "💳",
        }.get(ui_status, "🍽")
        table_name = str(table.get("name") or table.get("id"))
        lines = [f"{icon}  {table_name}", status_label]
        if guests:
            lines.append(_("restaurant.guests_count", guests=guests))
        elif seats:
            lines.append(_("restaurant.seats_count", seats=seats))
        if total not in (None, ""):
            lines.append(_("restaurant.table_total", total=_money(total)))
        if elapsed not in (None, ""):
            lines.append(_("restaurant.elapsed_minutes", minutes=elapsed))
        return "\n".join(lines)
