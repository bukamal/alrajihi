# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget
)

from i18n.translator import qt_layout_direction, translate as _


class RestaurantLineDialog(QDialog):
    """Small touch-safe dialog for adding a restaurant order line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("restaurant.add_item"))
        self.setMinimumWidth(420)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.qty_edit = QLineEdit("1")
        self.price_edit = QLineEdit("0")
        self.notes_edit = QLineEdit()
        for field in (self.name_edit, self.qty_edit, self.price_edit, self.notes_edit):
            field.setMinimumHeight(44)
        form.addRow(_("restaurant.item_name"), self.name_edit)
        form.addRow(_("quantity"), self.qty_edit)
        form.addRow(_("unit_price"), self.price_edit)
        form.addRow(_("notes"), self.notes_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        save = QPushButton(_("add"))
        cancel.setMinimumHeight(48)
        save.setMinimumHeight(48)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def payload(self):
        return {
            "item_name": self.name_edit.text().strip(),
            "quantity": self.qty_edit.text().strip() or "1",
            "unit_price": self.price_edit.text().strip() or "0",
            "notes": self.notes_edit.text().strip(),
        }


class RestaurantPaymentDialog(QDialog):
    """Touch-safe payment capture dialog for split restaurant payments."""

    def __init__(self, remaining="0", parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("restaurant.record_payment"))
        self.setMinimumWidth(420)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.amount_edit = QLineEdit(str(remaining or "0"))
        self.method_combo = QComboBox()
        self.method_combo.addItem(_("payment.cash"), "cash")
        self.method_combo.addItem(_("payment.card"), "card")
        self.method_combo.addItem(_("payment.bank"), "bank")
        self.notes_edit = QLineEdit()
        for field in (self.amount_edit, self.method_combo, self.notes_edit):
            field.setMinimumHeight(48)
        form.addRow(_("amount"), self.amount_edit)
        form.addRow(_("payment_method"), self.method_combo)
        form.addRow(_("notes"), self.notes_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        save = QPushButton(_("restaurant.record_payment"))
        cancel.setMinimumHeight(50)
        save.setMinimumHeight(50)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def payload(self):
        return {
            "amount": self.amount_edit.text().strip() or "0",
            "payment_method": self.method_combo.currentData() or "cash",
            "notes": self.notes_edit.text().strip(),
        }


class RestaurantPOSWidget(QWidget):
    sessionClosed = pyqtSignal()
    kitchenSent = pyqtSignal(dict)

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.session = None
        self.menu_items = []
        self.setObjectName("restaurantPOSWidget")
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        self.title = QLabel("🧾  " + _("restaurant.no_open_session"))
        self.title.setObjectName("restaurantPOSTitle")
        header.addWidget(self.title)
        header.addStretch()
        self.guests = QSpinBox()
        self.guests.setMinimum(1)
        self.guests.setMaximum(99)
        self.guests.setObjectName("restaurantGuestSpin")
        self.guests.setMinimumHeight(50)
        header.addWidget(QLabel(_("restaurant.guests")))
        header.addWidget(self.guests)
        root.addLayout(header)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("restaurantMenuSearch")
        self.search_edit.setPlaceholderText(_("restaurant.search_menu"))
        self.search_edit.setMinimumHeight(50)
        self.search_button = QPushButton("🔎  " + _("search"))
        self.search_button.setObjectName("restaurantMenuSearchButton")
        self.search_button.setMinimumHeight(50)
        self.manual_button = QPushButton("✍  " + _("restaurant.manual_item"))
        self.manual_button.setObjectName("restaurantManualItemButton")
        self.manual_button.setMinimumHeight(50)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.search_button)
        search_row.addWidget(self.manual_button)
        root.addLayout(search_row)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setObjectName("restaurantMenuScroll")
        self.menu_scroll.setWidgetResizable(True)
        self.menu_host = QWidget()
        self.menu_host.setObjectName("restaurantMenuHost")
        self.menu_grid = QGridLayout(self.menu_host)
        self.menu_grid.setContentsMargins(8, 8, 8, 8)
        self.menu_grid.setSpacing(12)
        self.menu_scroll.setWidget(self.menu_host)
        self.menu_scroll.setMinimumHeight(190)
        root.addWidget(self.menu_scroll)

        self.lines = QListWidget()
        self.lines.setObjectName("restaurantOrderLines")
        self.lines.setMinimumHeight(250)
        root.addWidget(self.lines)

        actions = QHBoxLayout()
        self.send_kitchen_btn = QPushButton("👨‍🍳  " + _("restaurant.send_to_kitchen"))
        self.payment_btn = QPushButton("💳  " + _("restaurant.record_payment"))
        self.close_btn = QPushButton("🧾  " + _("restaurant.checkout"))
        self.send_kitchen_btn.setObjectName("restaurantKitchenButton")
        self.payment_btn.setObjectName("restaurantPaymentButton")
        self.close_btn.setObjectName("restaurantCloseButton")
        for button in (self.send_kitchen_btn, self.payment_btn, self.close_btn):
            button.setMinimumHeight(66)
            actions.addWidget(button)
        root.addLayout(actions)

        self.total_label = QLabel(_("restaurant.current_total"))
        self.total_label.setObjectName("restaurantPOSTotal")
        root.addWidget(self.total_label)
        self.status = QLabel("")
        self.status.setObjectName("restaurantPOSStatus")
        root.addWidget(self.status)

        self.manual_button.clicked.connect(self.add_line)
        self.search_button.clicked.connect(self.reload_menu)
        self.search_edit.returnPressed.connect(self.reload_menu)
        self.send_kitchen_btn.clicked.connect(self.send_to_kitchen)
        self.payment_btn.clicked.connect(self.record_payment)
        self.close_btn.clicked.connect(self.checkout_session)
        self._set_enabled(False)
        self.reload_menu()

    def load_session(self, session):
        if not session:
            self.session = None
            self.title.setText("🧾  " + _("restaurant.no_open_session"))
            self.lines.clear()
            self._set_enabled(False)
            self._update_total()
            return
        self.session = self.service.get_session(int(session["id"]))
        table_name = self.session.get("table_name") or self.session.get("table_id") or ""
        self.title.setText("🧾  " + _("restaurant.active_session", table=table_name, session=self.session.get("id")))
        try:
            self.guests.setValue(int(self.session.get("guests") or 1))
        except Exception:
            self.guests.setValue(1)
        self._reload_lines()
        self._set_enabled(True)

    def _set_enabled(self, enabled):
        for widget in (self.send_kitchen_btn, self.payment_btn, self.close_btn, self.guests, self.manual_button):
            widget.setEnabled(bool(enabled))
        self.menu_scroll.setEnabled(bool(enabled))

    def reload_menu(self):
        try:
            self.menu_items = self.service.list_menu_items(search=self.search_edit.text().strip(), limit=36)
        except Exception as exc:
            self.menu_items = []
            self.status.setText(str(exc))
        self._render_menu_cards()

    def _clear_grid(self):
        while self.menu_grid.count():
            item = self.menu_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _render_menu_cards(self):
        self._clear_grid()
        if not self.menu_items:
            empty = QLabel(_("restaurant.no_menu_items"))
            empty.setObjectName("restaurantEmptyMenuLabel")
            empty.setAlignment(Qt.AlignCenter)
            self.menu_grid.addWidget(empty, 0, 0, 1, 3)
            return
        for index, item in enumerate(self.menu_items):
            button = QPushButton(self._menu_card_label(item))
            button.setObjectName("restaurantMenuItemButton")
            button.setMinimumSize(150, 96)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, payload=item: self.add_menu_item(payload))
            self.menu_grid.addWidget(button, index // 3, index % 3)

    def _menu_card_label(self, item):
        name = item.get("name") or item.get("item_name") or ""
        price = item.get("selling_price") or item.get("unit_price") or "0"
        unit = item.get("unit") or ""
        return f"🍽  {name}\n{price} {unit}".strip()

    def _reload_lines(self):
        self.lines.clear()
        for line in self.session.get("lines") or []:
            item = QListWidgetItem(self._line_label(line))
            item.setData(256, line)
            item.setData(257, line.get("kitchen_status") or "new")
            self.lines.addItem(item)
        self._update_total()

    def _line_label(self, line):
        status = line.get('kitchen_status') or 'new'
        return f"{line.get('quantity') or '1'} × {line.get('item_name') or ''} — {line.get('unit_price') or '0'} ({_(f'restaurant.line_status.{status}')})"

    def _line_amount(self, line):
        try:
            return Decimal(str(line.get("quantity") or "0")) * Decimal(str(line.get("unit_price") or "0"))
        except (InvalidOperation, TypeError):
            return Decimal("0")

    def _update_total(self):
        total = Decimal("0")
        if self.session:
            for line in self.session.get("lines") or []:
                total += self._line_amount(line)
        balance = self._balance() if self.session else {"paid": "0", "remaining": "0"}
        self.total_label.setText(_("restaurant.current_total") + f": {total}  |  " + _("restaurant.paid") + f": {balance.get('paid', '0')}  |  " + _("restaurant.remaining") + f": {balance.get('remaining', '0')}")

    def add_menu_item(self, item):
        if not self.session:
            self.status.setText(_("restaurant.open_table_first"))
            return
        try:
            self.service.add_line(
                session_id=int(self.session["id"]),
                item_id=item.get("id"),
                item_name=item.get("name") or item.get("item_name") or "",
                quantity="1",
                unit_price=item.get("selling_price") or item.get("unit_price") or "0",
                notes="",
            )
            self.load_session(self.session)
            self.status.setText(_("restaurant.line_added"))
        except Exception as exc:
            self.status.setText(str(exc))

    def add_line(self):
        if not self.session:
            return
        dialog = RestaurantLineDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        payload = dialog.payload()
        if not payload["item_name"]:
            self.status.setText(_("restaurant.item_required"))
            return
        try:
            self.service.add_line(session_id=int(self.session["id"]), **payload)
            self.load_session(self.session)
            self.status.setText(_("restaurant.line_added"))
        except Exception as exc:
            self.status.setText(str(exc))

    def send_to_kitchen(self):
        if not self.session:
            return
        try:
            result = self.service.send_to_kitchen(int(self.session["id"]))
            self.load_session(self.session)
            self.status.setText(_("restaurant.kitchen_sent"))
            self.kitchenSent.emit(result or {})
        except Exception as exc:
            self.status.setText(str(exc))

    def _balance(self):
        if not self.session:
            return {"total": "0", "paid": "0", "remaining": "0"}
        try:
            return self.service.session_balance(int(self.session["id"]))
        except Exception:
            return {"total": "0", "paid": "0", "remaining": "0"}

    def record_payment(self):
        if not self.session:
            return
        try:
            balance = self._balance()
            dialog = RestaurantPaymentDialog(balance.get("remaining") or "0", self)
            if dialog.exec() != QDialog.Accepted:
                return
            result = self.service.record_payment(session_id=int(self.session["id"]), **dialog.payload())
            self.load_session(self.session)
            remaining_label = _("restaurant.remaining")
            self.status.setText(_("restaurant.payment_recorded") + f" — {remaining_label}: {result.get('remaining', '0')}")
        except Exception as exc:
            self.status.setText(str(exc))

    def mark_payment_pending(self):
        # Backward-compatible slot; new UI records actual split payments.
        self.record_payment()

    def checkout_session(self):
        if not self.session:
            return
        try:
            result = self.service.checkout_session(int(self.session["id"]))
            reference = result.get("invoice_reference") or result.get("invoice_id") or ""
            self.status.setText(_("restaurant.checkout_done") + (f": {reference}" if reference else ""))
            self.session = None
            self.load_session(None)
            self.sessionClosed.emit()
        except Exception as exc:
            self.status.setText(str(exc))

    def close_session(self):
        # Backward-compatible alias for tests/plugins that still call the old slot.
        self.checkout_session()
