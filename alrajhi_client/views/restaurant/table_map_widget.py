# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from currency import currency
from i18n.translator import translate as _


def _money(value) -> str:
    try:
        return currency.format_display_amount(currency.to_display(Decimal(str(value or "0"))))
    except (InvalidOperation, TypeError, ValueError):
        return str(value or "0")


class RestaurantTableMapWidget(QWidget):
    tableClicked = pyqtSignal(dict)

    _STATUS_FILTERS = ("all", "free", "occupied", "kitchen", "ready", "payment", "reserved")

    def __init__(self, parent=None, density=None):
        super().__init__(parent)
        self.setObjectName("restaurantTableMap")
        self._density = (density or "touch").lower()
        self._tables: list[dict] = []
        self._visible_tables: list[dict] = []
        self._status_filter = "all"
        self._zone_filter = "all"
        self._search_text = ""

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("restaurantTableFilterBar")
        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(8, 6, 8, 6)
        filter_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("restaurantTableSearchInput")
        self.search_input.setPlaceholderText(_("restaurant.table_search_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("restaurantTableStatusFilter")
        for status in self._STATUS_FILTERS:
            self.status_filter.addItem(self._filter_status_label(status), status)
        self.status_filter.currentIndexChanged.connect(self._on_status_filter_changed)

        self.zone_filter = QComboBox()
        self.zone_filter.setObjectName("restaurantTableZoneFilter")
        self.zone_filter.addItem(_("restaurant.filter.all_zones"), "all")
        self.zone_filter.currentIndexChanged.connect(self._on_zone_filter_changed)

        filter_layout.addWidget(QLabel(_("restaurant.tables")))
        filter_layout.addWidget(self.search_input, 2)
        filter_layout.addWidget(self.status_filter, 1)
        filter_layout.addWidget(self.zone_filter, 1)
        root.addWidget(self.filter_bar)

        self.counter_bar = QFrame()
        self.counter_bar.setObjectName("restaurantTableCounterBar")
        counters = QHBoxLayout(self.counter_bar)
        counters.setContentsMargins(8, 2, 8, 2)
        counters.setSpacing(6)
        self.counter_labels: dict[str, QLabel] = {}
        for status in self._STATUS_FILTERS:
            label = QLabel()
            label.setObjectName(f"restaurantTableCounter_{status}")
            label.setProperty("restaurant_status", status)
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumHeight(28)
            self.counter_labels[status] = label
            counters.addWidget(label)
        root.addWidget(self.counter_bar)

        self.empty_label = QLabel(_("restaurant.table_filter_empty"))
        self.empty_label.setObjectName("restaurantTableEmptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setVisible(False)
        root.addWidget(self.empty_label)

        self._grid_container = QWidget()
        self._grid_container.setObjectName("restaurantTableGridContainer")
        self._layout = QGridLayout(self._grid_container)
        self._layout.setSpacing(14 if self._density == "compact" else 18)
        self._layout.setContentsMargins(2, 2, 2, 2)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("restaurantTableScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setWidget(self._grid_container)
        root.addWidget(self.scroll_area, 1)

    def set_density(self, density: str | None):
        self._density = (density or "touch").lower()
        self._layout.setSpacing(14 if self._density == "compact" else 18)
        self._apply_filters()

    def set_tables(self, tables):
        self._tables = list(tables or []) or self._default_tables()
        self._refresh_zone_filter()
        self._apply_filters()

    def _default_tables(self) -> list[dict]:
        return [
            {"id": index, "name": f"{_('restaurant.table')} {index}", "status": "free", "seats": 4, "zone": ""}
            for index in range(1, 13)
        ]

    def _columns(self) -> int:
        return 3 if self._density == "compact" else 4

    def _on_search_changed(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self._apply_filters()

    def _on_status_filter_changed(self) -> None:
        self._status_filter = self.status_filter.currentData() or "all"
        self._apply_filters()

    def _on_zone_filter_changed(self) -> None:
        self._zone_filter = self.zone_filter.currentData() or "all"
        self._apply_filters()

    def _refresh_zone_filter(self) -> None:
        current = self.zone_filter.currentData() or self._zone_filter or "all"
        self.zone_filter.blockSignals(True)
        self.zone_filter.clear()
        self.zone_filter.addItem(_("restaurant.filter.all_zones"), "all")
        zones = sorted({self._zone_name(table) for table in self._tables if self._zone_name(table)})
        for zone in zones:
            self.zone_filter.addItem(zone, zone)
        index = self.zone_filter.findData(current)
        self.zone_filter.setCurrentIndex(index if index >= 0 else 0)
        self.zone_filter.blockSignals(False)
        self._zone_filter = self.zone_filter.currentData() or "all"

    def _clear_grid(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _apply_filters(self) -> None:
        self._visible_tables = [table for table in self._tables if self._matches_filters(table)]
        self._clear_grid()
        self._update_counters()
        self.empty_label.setVisible(not bool(self._visible_tables))
        for index, table in enumerate(self._visible_tables):
            button = self._button(table)
            self._layout.addWidget(button, index // self._columns(), index % self._columns())
        self._grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _matches_filters(self, table: dict) -> bool:
        ui_status = self._ui_status(table)
        if self._status_filter != "all" and ui_status != self._status_filter:
            return False
        zone = self._zone_name(table)
        if self._zone_filter != "all" and zone != self._zone_filter:
            return False
        if not self._search_text:
            return True
        haystack = " ".join(
            str(part or "")
            for part in (
                table.get("id"),
                table.get("name"),
                table.get("code"),
                table.get("label"),
                zone,
                self._status_label(ui_status),
            )
        ).lower()
        return self._search_text in haystack

    def _zone_name(self, table: dict) -> str:
        return str(table.get("zone") or table.get("area") or table.get("floor") or table.get("section") or "").strip()

    def _filter_status_label(self, status: str) -> str:
        if status == "all":
            return _("restaurant.filter.all_statuses")
        return self._status_label(status)

    def _button(self, table):
        button = QPushButton(self._label(table))
        button.setObjectName("restaurantTableButton")
        button.setMinimumSize(156, 112) if self._density == "compact" else button.setMinimumSize(178, 128)
        button.setCursor(Qt.PointingHandCursor)
        button.setProperty("restaurant_status", self._ui_status(table))
        button.clicked.connect(lambda _=False, t=table: self.tableClicked.emit(t))
        return button

    def _ui_status(self, table):
        rich_status = str(
            table.get("ui_status")
            or table.get("table_state")
            or table.get("active_table_state")
            or table.get("active_order_state")
            or table.get("active_kitchen_status")
            or ""
        ).lower()
        if rich_status in {"free", "occupied", "kitchen", "ready", "payment", "reserved"}:
            return rich_status
        status = str(table.get("status") or "free").lower()
        kitchen_status = str(table.get("kitchen_status") or table.get("active_kitchen_state") or "").lower()
        if status == "occupied" and kitchen_status in {"kitchen", "sent", "preparing", "waiting_kitchen"}:
            return "kitchen"
        if status == "occupied" and kitchen_status in {"ready"}:
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

    def _update_counters(self) -> None:
        counts = {status: 0 for status in self._STATUS_FILTERS}
        counts["all"] = len(self._tables)
        for table in self._tables:
            status = self._ui_status(table)
            counts[status] = counts.get(status, 0) + 1
        for status, label in self.counter_labels.items():
            label.setText(f"{self._filter_status_label(status)}: {counts.get(status, 0)}")

    def _label(self, table):
        ui_status = self._ui_status(table)
        status_label = self._status_label(ui_status)
        guests = table.get("active_guests") or table.get("guests") or ""
        seats = table.get("seats") or ""
        total = table.get("active_total") or table.get("total") or table.get("balance_total")
        elapsed = table.get("elapsed_minutes") or table.get("age_minutes")
        zone = self._zone_name(table)
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
        if zone:
            lines.append(zone)
        if guests:
            lines.append(_("restaurant.guests_count", guests=guests))
        elif seats:
            lines.append(_("restaurant.seats_count", seats=seats))
        if total not in (None, ""):
            lines.append(_("restaurant.table_total", total=_money(total)))
        if elapsed not in (None, ""):
            lines.append(_("restaurant.elapsed_minutes", minutes=elapsed))
        return "\n".join(lines)
