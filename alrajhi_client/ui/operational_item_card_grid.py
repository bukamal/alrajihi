# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QGridLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)


def _decimal(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


class OperationalItemCardGrid(QWidget):
    """Shared POS/Restaurant/Cafe material-card surface.

    The widget intentionally owns only the visual grid and activation signal.
    It does not mutate carts, orders, invoices, stock, payment, or printing.
    Phase428 default: three material columns, responsive fallback to 2/4.
    """

    itemActivated = pyqtSignal(object)

    def __init__(
        self,
        parent=None,
        *,
        mode: str = "pos",
        default_columns: int = 3,
        min_columns: int = 2,
        max_columns: int = 4,
        empty_text: str = "لا توجد مواد",
        money_formatter: Callable[[Any], str] | None = None,
        icon: str = "",
    ):
        super().__init__(parent)
        self.mode = str(mode or "pos")
        self.default_columns = max(1, int(default_columns or 3))
        self.min_columns = max(1, int(min_columns or 1))
        self.max_columns = max(self.default_columns, int(max_columns or self.default_columns))
        self.empty_text = empty_text
        self.money_formatter = money_formatter
        self.icon = icon
        self._items: list[dict[str, Any]] = []
        self._columns = self.default_columns
        self.setObjectName("operationalItemCardGrid")
        self.setProperty("operationalItemCardGrid", True)
        self.setProperty("operational_mode", self.mode)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("operationalItemCardScroll")
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.host.setObjectName("operationalItemCardHost")
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        self.scroll.setWidget(self.host)
        layout.addWidget(self.scroll)

    def set_items(self, items: Iterable[dict[str, Any]] | None) -> None:
        self._items = [dict(item or {}) for item in (items or [])]
        self._render()

    def items(self) -> list[dict[str, Any]]:
        return list(self._items)

    def clear(self) -> None:
        self.set_items([])

    def columns_for_width(self, width: int | None = None) -> int:
        width = int(width if width is not None else self.scroll.viewport().width())
        if width <= 0:
            return self.default_columns
        if width < 420:
            return max(1, min(self.default_columns, self.min_columns))
        if width >= 940 and self.max_columns > self.default_columns:
            return self.max_columns
        return self.default_columns

    def relayout(self) -> None:
        columns = self.columns_for_width()
        if columns != self._columns:
            self._columns = columns
            self._render()

    def resizeEvent(self, event):  # pragma: no cover - Qt callback
        super().resizeEvent(event)
        self.relayout()

    def _clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _price_value(self, item: dict[str, Any]) -> Any:
        return (
            item.get("selling_price")
            or item.get("unit_price")
            or item.get("price")
            or item.get("sale_price")
            or "0"
        )

    def _format_price(self, value: Any) -> str:
        if self.money_formatter is not None:
            try:
                return self.money_formatter(value)
            except Exception:
                pass
        value = _decimal(value)
        return f"{value:,.2f}"

    def _card_label(self, item: dict[str, Any]) -> str:
        name = (
            item.get("name")
            or item.get("item_name")
            or item.get("product_name")
            or item.get("description")
            or ""
        )
        unit = item.get("unit") or item.get("unit_name") or item.get("base_unit") or ""
        barcode = item.get("barcode") or item.get("matched_barcode") or ""
        prefix = (self.icon + "  ") if self.icon else ""
        lines = [f"{prefix}{name}".strip(), self._format_price(self._price_value(item))]
        if unit:
            lines.append(str(unit))
        if self.mode == "pos" and barcode:
            lines.append(str(barcode))
        return "\n".join([line for line in lines if line])

    def _render_empty(self) -> None:
        empty = QLabel(self.empty_text)
        empty.setObjectName("operationalItemCardEmpty")
        empty.setAlignment(Qt.AlignCenter)
        empty.setWordWrap(True)
        self.grid.addWidget(empty, 0, 0, 1, max(1, self._columns))

    def _render(self) -> None:
        self._clear_grid()
        self._columns = self.columns_for_width()
        if not self._items:
            self._render_empty()
            return
        for index, item in enumerate(self._items):
            button = QPushButton(self._card_label(item))
            button.setObjectName("operationalItemCardButton")
            button.setProperty("operationalItemCard", True)
            button.setProperty("operational_mode", self.mode)
            button.setProperty("basitCard", True)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(74 if self.mode in {"restaurant", "cafe"} else 66)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(lambda _=False, payload=item: self.itemActivated.emit(dict(payload)))
            self.grid.addWidget(button, index // self._columns, index % self._columns)
        self.grid.setRowStretch((len(self._items) + self._columns - 1) // self._columns, 1)
