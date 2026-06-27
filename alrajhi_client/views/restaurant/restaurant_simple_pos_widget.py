# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.services.restaurant_operation_policy import restaurant_operation_policy
from core.services.restaurant_service import restaurant_service
from currency import currency
from features.restaurant.restaurant_printing_bridge import restaurant_printing_bridge
from i18n.translator import qt_layout_direction, translate as _
from workspace.operational.operational_shell_contract import bind_operational_shell
from ui.table_direction_policy import apply_table_direction


def _dec(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _money(value: Any) -> str:
    try:
        return currency.format_display_amount(currency.to_display(_dec(value)))
    except Exception:
        return str(value or "0")


class RestaurantSimplePOSWidget(QWidget):
    """Simple restaurant selling interface backed by the restaurant/POS engine.

    Phase 394 deliberately removes the exposed table/kitchen/KDS workflow from
    the default restaurant workspace.  The operator sees three surfaces only:
    categories, menu items, and the current invoice table.  The checkout path
    still records a normal sale invoice through the restaurant gateway.
    """

    sessionClosed = pyqtSignal()

    def __init__(self, parent=None, service=None):
        super().__init__(parent)
        bind_operational_shell(self, 'restaurant')
        self.service = service or restaurant_service
        self.session: dict[str, Any] | None = None
        self.categories: list[dict[str, Any]] = []
        self.menu_items: list[dict[str, Any]] = []
        self.current_category_id: int | None = None
        self._loading_lines = False
        self.setObjectName("restaurantSimplePOSWidget")
        self.setProperty("restaurant_simple_pos", True)
        self.setProperty("basitInspired", True)
        self.setLayoutDirection(qt_layout_direction())
        self._build_ui()
        self.reload_categories()
        self.reload_menu()
        self._refresh_invoice()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header_card = QFrame()
        header_card.setObjectName("restaurantSimpleHeaderCard")
        header = QHBoxLayout(header_card)
        header.setContentsMargins(14, 8, 14, 8)
        header.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title = QLabel("🍽  " + _("restaurant.simple_pos_title"))
        self.title.setObjectName("restaurantSimpleTitle")
        self.subtitle = QLabel(_("restaurant.simple_pos_subtitle"))
        self.subtitle.setObjectName("restaurantSimpleSubtitle")
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box, 2)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("restaurantSimpleSearch")
        self.search_edit.setPlaceholderText(_("restaurant.simple_search_placeholder"))
        self.search_edit.setMinimumHeight(46)
        self.search_btn = QPushButton("🔎  " + _("search"))
        self.search_btn.setObjectName("restaurantSimpleSearchButton")
        self.search_btn.setMinimumHeight(46)
        self.search_btn.setProperty("basitToolbarButton", True)
        self.new_sale_btn = QPushButton("➕  " + _("restaurant.simple_new_sale"))
        self.new_sale_btn.setObjectName("restaurantSimpleNewSaleButton")
        self.new_sale_btn.setMinimumHeight(46)
        self.new_sale_btn.setProperty("basitToolbarButton", True)
        self.refresh_btn = QPushButton("↻  " + _("common.refresh"))
        self.refresh_btn.setObjectName("restaurantSimpleRefreshButton")
        self.refresh_btn.setMinimumHeight(46)
        self.refresh_btn.setProperty("basitToolbarButton", True)
        header.addWidget(self.search_edit, 3)
        header.addWidget(self.search_btn)
        header.addWidget(self.new_sale_btn)
        header.addWidget(self.refresh_btn)
        root.addWidget(header_card)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("restaurantSimpleThreeSectionSplitter")
        self.splitter.addWidget(self._build_category_section())
        self.splitter.addWidget(self._build_items_section())
        self.splitter.addWidget(self._build_invoice_section())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 3)
        self.splitter.setSizes([270, 360, 720])
        root.addWidget(self.splitter, 1)

        self.status = QLabel("")
        self.status.setObjectName("restaurantSimpleStatus")
        root.addWidget(self.status)

        self.search_btn.clicked.connect(self.reload_menu)
        self.search_edit.returnPressed.connect(self.reload_menu)
        self.refresh_btn.clicked.connect(self.reload)
        self.new_sale_btn.clicked.connect(self.start_new_sale)
        self.qty_plus_btn.clicked.connect(lambda: self.adjust_selected_quantity(Decimal("1")))
        self.qty_minus_btn.clicked.connect(lambda: self.adjust_selected_quantity(Decimal("-1")))
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        self.print_btn.clicked.connect(self.print_receipt)
        self.checkout_btn.clicked.connect(self.checkout_current_sale)
        self.invoice_table.itemChanged.connect(self._invoice_item_changed)

    def _section_frame(self, title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("restaurantSimpleSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("restaurantSimpleSectionTitle")
        layout.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("restaurantSimpleSectionSubtitle")
            sub.setWordWrap(True)
            layout.addWidget(sub)
        return frame, layout

    def _build_category_section(self) -> QFrame:
        frame, layout = self._section_frame("①  " + _("restaurant.simple_categories"), _("restaurant.simple_categories_help"))
        self.category_scroll = QScrollArea()
        self.category_scroll.setObjectName("restaurantSimpleCategoryScroll")
        self.category_scroll.setWidgetResizable(True)
        self.category_host = QWidget()
        self.category_grid = QGridLayout(self.category_host)
        self.category_grid.setContentsMargins(0, 0, 0, 0)
        self.category_grid.setSpacing(8)
        self.category_scroll.setWidget(self.category_host)
        layout.addWidget(self.category_scroll, 1)
        return frame

    def _build_items_section(self) -> QFrame:
        frame, layout = self._section_frame("②  " + _("restaurant.simple_items"), _("restaurant.simple_items_help"))
        self.items_scroll = QScrollArea()
        self.items_scroll.setObjectName("restaurantSimpleItemsScroll")
        self.items_scroll.setWidgetResizable(True)
        self.items_host = QWidget()
        self.items_grid = QGridLayout(self.items_host)
        self.items_grid.setContentsMargins(0, 0, 0, 0)
        self.items_grid.setSpacing(10)
        self.items_scroll.setWidget(self.items_host)
        layout.addWidget(self.items_scroll, 1)
        return frame

    def _build_invoice_section(self) -> QFrame:
        frame, layout = self._section_frame("③  " + _("restaurant.simple_invoice"), _("restaurant.simple_invoice_help"))
        self.invoice_table = QTableWidget(0, 5)
        apply_table_direction(self.invoice_table)
        self.invoice_table.setObjectName("restaurantSimpleInvoiceTable")
        self.invoice_table.setProperty("basitTable", True)
        self.invoice_table.setHorizontalHeaderLabels([
            _("item_name_header"), _("quantity"), _("unit_price"), _("total"), _("notes"),
        ])
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.invoice_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked)
        header = self.invoice_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.invoice_table, 1)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.qty_minus_btn = QPushButton("−")
        self.qty_minus_btn.setObjectName("restaurantSimpleQtyMinusButton")
        self.qty_plus_btn = QPushButton("+")
        self.qty_plus_btn.setObjectName("restaurantSimpleQtyPlusButton")
        self.remove_line_btn = QPushButton("🗑  " + _("delete"))
        self.remove_line_btn.setObjectName("restaurantSimpleRemoveLineButton")
        for button in (self.qty_minus_btn, self.qty_plus_btn, self.remove_line_btn):
            button.setMinimumHeight(44)
        controls.addWidget(self.qty_minus_btn)
        controls.addWidget(self.qty_plus_btn)
        controls.addWidget(self.remove_line_btn)
        controls.addStretch(1)
        layout.addLayout(controls)

        footer = QFrame()
        footer.setObjectName("restaurantSimpleFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 8, 10, 8)
        footer_layout.setSpacing(10)
        self.total_label = QLabel(_("restaurant.simple_total") + ": " + _money("0"))
        self.total_label.setObjectName("restaurantSimpleTotal")
        self.total_label.setProperty("basitTotal", True)
        self.print_btn = QPushButton("🧾  " + _("restaurant.print_receipt"))
        self.print_btn.setObjectName("restaurantSimplePrintButton")
        self.checkout_btn = QPushButton("💳  " + _("restaurant.simple_checkout"))
        self.checkout_btn.setObjectName("restaurantSimpleCheckoutButton")
        for button in (self.print_btn, self.checkout_btn):
            button.setMinimumHeight(58)
            button.setMinimumWidth(160)
        footer_layout.addWidget(self.total_label, 1)
        footer_layout.addWidget(self.print_btn)
        footer_layout.addWidget(self.checkout_btn)
        layout.addWidget(footer)
        return frame

    def reload(self) -> None:
        self.reload_categories()
        self.reload_menu()
        self._refresh_invoice()

    def refresh(self) -> None:
        self.reload()

    def _clear_layout(self, layout: QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def reload_categories(self) -> None:
        try:
            self.categories = self.service.list_menu_categories(search="", limit=120)
        except Exception as exc:
            self.categories = []
            self.status.setText(str(exc))
        self._render_categories()

    def _render_categories(self) -> None:
        self._clear_layout(self.category_grid)
        all_payload = {"id": None, "name": _("all"), "item_count": len(self.menu_items or [])}
        rows = [all_payload] + list(self.categories or [])
        for index, category in enumerate(rows):
            name = category.get("name") or category.get("full_name") or _("categories")
            count = category.get("item_count")
            text = f"{name}" + (f"\n{count}" if count not in (None, "") else "")
            button = QPushButton(text)
            button.setObjectName("restaurantSimpleCategoryButton")
            button.setProperty("basitCard", True)
            button.setCheckable(True)
            button.setChecked((category.get("id") or None) == self.current_category_id)
            button.setMinimumHeight(58)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(lambda _=False, payload=category: self.select_category(payload.get("id")))
            self.category_grid.addWidget(button, index, 0)
        self.category_grid.setRowStretch(len(rows), 1)

    def select_category(self, category_id: Any) -> None:
        self.current_category_id = int(category_id) if category_id not in (None, "", 0, "0") else None
        self.reload_menu()
        self._render_categories()

    def reload_menu(self) -> None:
        try:
            self.menu_items = self.service.list_menu_items(
                search=self.search_edit.text().strip(),
                category_id=self.current_category_id,
                limit=96,
            )
        except Exception as exc:
            self.menu_items = []
            self.status.setText(str(exc))
        self._render_items()

    def _render_items(self) -> None:
        self._clear_layout(self.items_grid)
        if not self.menu_items:
            empty = QLabel(_("restaurant.no_menu_items"))
            empty.setObjectName("restaurantSimpleEmptyItems")
            empty.setAlignment(Qt.AlignCenter)
            self.items_grid.addWidget(empty, 0, 0)
            return
        # Phase396: menu items intentionally mirror the category surface:
        # one full-width rectangular card per row.  The restaurant screen is
        # a simple POS, so product discovery should feel identical to category
        # selection instead of using a separate multi-column tile grammar.
        for index, item in enumerate(self.menu_items):
            name = item.get("name") or item.get("item_name") or ""
            price = item.get("selling_price") or item.get("unit_price") or "0"
            unit = item.get("unit") or ""
            text = f"{name}\n{_money(price)}" + (f"\n{unit}" if unit else "")
            button = QPushButton(text)
            button.setObjectName("restaurantSimpleItemButton")
            button.setProperty("restaurant_same_card_surface", True)
            button.setProperty("basitCard", True)
            button.setMinimumHeight(64)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, payload=item: self.add_item(payload))
            self.items_grid.addWidget(button, index, 0)
        self.items_grid.setRowStretch(len(self.menu_items), 1)

    def resizeEvent(self, event):  # pragma: no cover - Qt callback
        super().resizeEvent(event)

    def start_new_sale(self) -> None:
        try:
            self.session = self.service.create_takeaway_order(notes="restaurant_simple_pos")
            self.status.setText(_("restaurant.simple_sale_started", session=self.session.get("id")))
            self._refresh_invoice()
        except Exception as exc:
            self.status.setText(str(exc))

    def _ensure_session(self) -> dict[str, Any] | None:
        if self.session and self.session.get("id"):
            return self.session
        self.start_new_sale()
        return self.session

    def _load_current_session(self) -> None:
        if self.session and self.session.get("id"):
            self.session = self.service.get_session(int(self.session["id"]))

    def add_item(self, item: dict[str, Any]) -> None:
        if not restaurant_operation_policy.can(restaurant_operation_policy.OP_ADD_LINE):
            self.status.setText(restaurant_operation_policy.denial_message(restaurant_operation_policy.OP_ADD_LINE))
            return
        session = self._ensure_session()
        if not session:
            return
        try:
            self._load_current_session()
            existing = self._find_existing_line(item)
            if existing:
                new_qty = _dec(existing.get("quantity"), "0") + Decimal("1")
                self.service.update_order_line(int(existing["id"]), quantity=str(new_qty))
            else:
                self.service.add_line(
                    session_id=int(self.session["id"]),
                    item_id=item.get("id"),
                    item_name=item.get("name") or item.get("item_name") or "",
                    quantity="1",
                    unit_price=item.get("selling_price") or item.get("unit_price") or "0",
                    notes="",
                    unit_id=item.get("unit_id"),
                    unit=item.get("unit") or "",
                    conversion_factor=item.get("conversion_factor") or "1",
                    base_qty="1",
                    barcode_scope=item.get("barcode_scope") or "menu",
                    matched_barcode=item.get("barcode") or "",
                )
            self._refresh_invoice()
            self.status.setText(_("restaurant.simple_item_added"))
        except Exception as exc:
            self.status.setText(str(exc))

    def _find_existing_line(self, item: dict[str, Any]) -> dict[str, Any] | None:
        item_id = item.get("id")
        for line in (self.session or {}).get("lines") or []:
            if str(line.get("kitchen_status") or "new").lower() == "cancelled":
                continue
            if item_id and str(line.get("item_id") or "") == str(item_id):
                return line
        return None

    def _refresh_invoice(self) -> None:
        if self.session and self.session.get("id"):
            try:
                self._load_current_session()
            except Exception as exc:
                self.status.setText(str(exc))
        lines = [line for line in ((self.session or {}).get("lines") or []) if str(line.get("kitchen_status") or "new").lower() != "cancelled"]
        self._loading_lines = True
        try:
            self.invoice_table.setRowCount(0)
            for row, line in enumerate(lines):
                self.invoice_table.insertRow(row)
                self._set_line_row(row, line)
        finally:
            self._loading_lines = False
        self._update_total()
        has_lines = bool(lines)
        for widget in (self.qty_minus_btn, self.qty_plus_btn, self.remove_line_btn, self.print_btn, self.checkout_btn):
            widget.setEnabled(has_lines)

    def _set_line_row(self, row: int, line: dict[str, Any]) -> None:
        values = [
            line.get("item_name") or "",
            str(line.get("quantity") or "1"),
            _money(line.get("unit_price") or "0"),
            _money(line.get("line_total") or (_dec(line.get("quantity"), "0") * _dec(line.get("unit_price"), "0"))),
            line.get("notes") or "",
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            item.setData(Qt.UserRole, line.get("id"))
            if column in (0, 2, 3):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.invoice_table.setItem(row, column, item)

    def _selected_line_id(self) -> int | None:
        indexes = self.invoice_table.selectionModel().selectedRows() if self.invoice_table.selectionModel() else []
        if not indexes:
            row = self.invoice_table.currentRow()
        else:
            row = indexes[0].row()
        if row is None or row < 0:
            return None
        item = self.invoice_table.item(row, 0) or self.invoice_table.item(row, 1)
        try:
            line_id = int(item.data(Qt.UserRole) or 0) if item else 0
            return line_id if line_id > 0 else None
        except Exception:
            return None

    def _line_by_id(self, line_id: int | None) -> dict[str, Any] | None:
        if not line_id:
            return None
        for line in (self.session or {}).get("lines") or []:
            try:
                if int(line.get("id") or 0) == int(line_id):
                    return line
            except Exception:
                pass
        return None

    def adjust_selected_quantity(self, delta: Decimal) -> None:
        line_id = self._selected_line_id()
        line = self._line_by_id(line_id)
        if not line:
            self.status.setText(_("restaurant.simple_select_line"))
            return
        try:
            qty = _dec(line.get("quantity"), "1") + delta
            if qty <= Decimal("0"):
                self.service.update_line_status(int(line_id), "cancelled")
            else:
                self.service.update_order_line(int(line_id), quantity=str(qty))
            self._refresh_invoice()
        except Exception as exc:
            self.status.setText(str(exc))

    def remove_selected_line(self) -> None:
        line_id = self._selected_line_id()
        if not line_id:
            self.status.setText(_("restaurant.simple_select_line"))
            return
        try:
            self.service.update_line_status(int(line_id), "cancelled")
            self._refresh_invoice()
        except Exception as exc:
            self.status.setText(str(exc))

    def _invoice_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading_lines or item is None:
            return
        if item.column() not in (1, 4):
            return
        line_id = self._selected_line_id() or item.data(Qt.UserRole)
        if not line_id:
            return
        try:
            if item.column() == 1:
                qty = _dec(item.text(), "1")
                if qty <= Decimal("0"):
                    self.service.update_line_status(int(line_id), "cancelled")
                else:
                    self.service.update_order_line(int(line_id), quantity=str(qty))
            elif item.column() == 4:
                self.service.update_order_line(int(line_id), notes=item.text().strip())
            self._refresh_invoice()
        except Exception as exc:
            self.status.setText(str(exc))
            self._refresh_invoice()

    def _update_total(self) -> None:
        total = Decimal("0")
        if self.session and self.session.get("id"):
            try:
                balance = self.service.session_balance(int(self.session["id"]))
                total = _dec(balance.get("total"), "0")
            except Exception:
                for line in (self.session.get("lines") or []):
                    if str(line.get("kitchen_status") or "new").lower() != "cancelled":
                        total += _dec(line.get("line_total") or (_dec(line.get("quantity"), "0") * _dec(line.get("unit_price"), "0")))
        self.total_label.setText(_("restaurant.simple_total") + ": " + _money(total))

    def print_receipt(self) -> None:
        if not self.session:
            return
        try:
            self.service.mark_session_lines_served(int(self.session["id"]))
            if restaurant_printing_bridge.receipt_print(int(self.session["id"]), self):
                self.status.setText(_("restaurant.receipt_printed"))
            self._refresh_invoice()
        except Exception as exc:
            self.status.setText(str(exc))

    def checkout_current_sale(self) -> None:
        if not self.session:
            return
        if not restaurant_operation_policy.can(restaurant_operation_policy.OP_CHECKOUT):
            self.status.setText(restaurant_operation_policy.denial_message(restaurant_operation_policy.OP_CHECKOUT))
            return
        try:
            result = self.service.checkout_simple_pos_session(int(self.session["id"]), payment_method="cash")
            reference = result.get("invoice_reference") or result.get("invoice_id") or ""
            self.status.setText(_("restaurant.checkout_done") + (f": {reference}" if reference else ""))
            self.session = None
            self._refresh_invoice()
            self.sessionClosed.emit()
        except Exception as exc:
            self.status.setText(str(exc))
