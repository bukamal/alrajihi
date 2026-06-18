# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget
)

from i18n.translator import qt_layout_direction, translate as _
from core.services.barcode_input_service import barcode_input_service
from core.services.restaurant_operation_policy import restaurant_operation_policy
from core.services.settings_service import settings_service
from features.restaurant.restaurant_printing_bridge import restaurant_printing_bridge
from features.restaurant.restaurant_order_grid import RestaurantOrderGrid
from features.restaurant.restaurant_order_model import RestaurantOrderModel


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


class RestaurantAdjustmentsDialog(QDialog):
    """Touch-safe bill adjustments: discount, service charge, and tax."""

    def __init__(self, balance=None, parent=None):
        super().__init__(parent)
        balance = balance or {}
        self.setWindowTitle(_("restaurant.adjust_bill"))
        self.setMinimumWidth(440)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.discount_edit = QLineEdit(str(balance.get("discount_amount") or "0"))
        self.service_edit = QLineEdit(str(balance.get("service_charge_amount") or "0"))
        self.tax_edit = QLineEdit(str(balance.get("tax_amount") or "0"))
        self.notes_edit = QLineEdit(str(balance.get("adjustment_notes") or ""))
        for field in (self.discount_edit, self.service_edit, self.tax_edit, self.notes_edit):
            field.setMinimumHeight(48)
        form.addRow(_("restaurant.discount"), self.discount_edit)
        form.addRow(_("restaurant.service_charge"), self.service_edit)
        form.addRow(_("restaurant.tax"), self.tax_edit)
        form.addRow(_("notes"), self.notes_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        save = QPushButton(_("save"))
        cancel.setMinimumHeight(50)
        save.setMinimumHeight(50)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def payload(self):
        return {
            "discount_amount": self.discount_edit.text().strip() or "0",
            "service_charge_amount": self.service_edit.text().strip() or "0",
            "tax_amount": self.tax_edit.text().strip() or "0",
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
        self.search_edit.setPlaceholderText(_("restaurant.search_menu_or_barcode"))
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

        self.order_model = RestaurantOrderModel([], parent=self)
        self.lines = RestaurantOrderGrid(self)
        self.lines.setObjectName("restaurantOrderLines")
        self.lines.setModel(self.order_model)
        self.lines.setMinimumHeight(250)
        root.addWidget(self.lines)

        actions = QHBoxLayout()
        self.send_kitchen_btn = QPushButton("👨‍🍳  " + _("restaurant.send_to_kitchen"))
        self.print_kitchen_btn = QPushButton("🖨  " + _("restaurant.print_kitchen_ticket"))
        self.adjust_btn = QPushButton("%  " + _("restaurant.adjust_bill"))
        self.payment_btn = QPushButton("💳  " + _("restaurant.record_payment"))
        self.print_receipt_btn = QPushButton("🧾  " + _("restaurant.print_receipt"))
        self.close_btn = QPushButton("✅  " + _("restaurant.checkout"))
        self.send_kitchen_btn.setObjectName("restaurantKitchenButton")
        self.print_kitchen_btn.setObjectName("restaurantKitchenPrintButton")
        self.adjust_btn.setObjectName("restaurantAdjustButton")
        self.payment_btn.setObjectName("restaurantPaymentButton")
        self.print_receipt_btn.setObjectName("restaurantReceiptPrintButton")
        self.close_btn.setObjectName("restaurantCloseButton")
        for button in (self.send_kitchen_btn, self.print_kitchen_btn, self.adjust_btn, self.payment_btn, self.print_receipt_btn, self.close_btn):
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
        self.search_edit.returnPressed.connect(self.handle_entry_return)
        self.send_kitchen_btn.clicked.connect(self.send_to_kitchen)
        self.print_kitchen_btn.clicked.connect(self.print_last_kitchen_ticket)
        self.adjust_btn.clicked.connect(self.adjust_bill)
        self.payment_btn.clicked.connect(self.record_payment)
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        self.close_btn.clicked.connect(self.checkout_session)
        self._set_enabled(False)
        self.reload_menu()

    def load_session(self, session):
        if not session:
            self.session = None
            self.title.setText("🧾  " + _("restaurant.no_open_session"))
            self.order_model.set_lines([])
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
        for widget in (self.send_kitchen_btn, self.print_kitchen_btn, self.adjust_btn, self.payment_btn, self.print_receipt_btn, self.close_btn, self.guests, self.manual_button):
            widget.setEnabled(bool(enabled))
        self.menu_scroll.setEnabled(bool(enabled))
        self._apply_restaurant_operation_state()

    def _operation_button_map(self):
        return {
            restaurant_operation_policy.OP_ADD_LINE: [self.manual_button],
            restaurant_operation_policy.OP_SEND_KITCHEN: [self.send_kitchen_btn],
            restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET: [self.print_kitchen_btn],
            restaurant_operation_policy.OP_ADJUST_BILL: [self.adjust_btn],
            restaurant_operation_policy.OP_RECORD_PAYMENT: [self.payment_btn],
            restaurant_operation_policy.OP_PRINT_RECEIPT: [self.print_receipt_btn],
            restaurant_operation_policy.OP_CHECKOUT: [self.close_btn],
        }

    def _apply_restaurant_operation_state(self):
        has_session = bool(self.session)
        for operation, buttons in self._operation_button_map().items():
            allowed = has_session and restaurant_operation_policy.can(operation)
            for button in buttons:
                button.setVisible(restaurant_operation_policy.is_enabled_by_settings(operation))
                button.setEnabled(bool(allowed))

    def _require_restaurant_operation(self, operation):
        try:
            restaurant_operation_policy.require(operation)
            return True
        except Exception as exc:
            self.status.setText(str(exc))
            return False

    def handle_entry_return(self):
        text = self.search_edit.text().strip()
        if not text:
            self.reload_menu()
            return
        normalized = barcode_input_service.normalize(text)
        scan_like = barcode_input_service.looks_like_scan(normalized)
        if not self.session:
            self.reload_menu()
            if scan_like:
                self.status.setText(_("restaurant.open_table_first"))
            return
        if scan_like and not self._require_restaurant_operation(restaurant_operation_policy.OP_ADD_LINE):
            return
        if not scan_like:
            self.reload_menu()
            return
        try:
            self.service.add_entry(session_id=int(self.session["id"]), raw_entry=text, quantity="1", mode="scan")
            self.search_edit.clear()
            self.load_session(self.session)
            self.status.setText(_("restaurant.barcode_line_added"))
        except Exception as exc:
            key = str(exc)
            self.status.setText(_(key) if key.startswith(("transaction_", "restaurant.")) else key)

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
        self.order_model.set_lines(self.session.get("lines") or [])
        try:
            self.lines.apply_named_preset("cashier")
        except Exception:
            pass
        self._update_total()

    def _line_label(self, line):
        status = line.get('kitchen_status') or 'new'
        unit = line.get('unit') or ''
        scope = line.get('barcode_scope') or ''
        base_qty = line.get('base_qty') or ''
        unit_part = f" {unit}" if unit else ""
        barcode_part = ""
        if scope == "unit":
            barcode_part = f" — {_('restaurant.unit_barcode_scope')}"
            if base_qty:
                barcode_part += f" / {_('pos_column_base_qty')}: {base_qty}"
        return f"{line.get('quantity') or '1'}{unit_part} × {line.get('item_name') or ''} — {line.get('unit_price') or '0'} ({_(f'restaurant.line_status.{status}')}){barcode_part}"

    def _line_amount(self, line):
        try:
            return Decimal(str(line.get("quantity") or "0")) * Decimal(str(line.get("unit_price") or "0"))
        except (InvalidOperation, TypeError):
            return Decimal("0")

    def _update_total(self):
        subtotal = Decimal("0")
        if self.session:
            for line in self.session.get("lines") or []:
                subtotal += self._line_amount(line)
        balance = self._balance() if self.session else {"total": str(subtotal), "paid": "0", "remaining": "0", "discount_amount": "0", "service_charge_amount": "0", "tax_amount": "0"}
        self.total_label.setText(
            _("restaurant.subtotal") + f": {balance.get('subtotal', subtotal)}  |  "
            + _("restaurant.discount") + f": {balance.get('discount_amount', '0')}  |  "
            + _("restaurant.service_charge") + f": {balance.get('service_charge_amount', '0')}  |  "
            + _("restaurant.tax") + f": {balance.get('tax_amount', '0')}  |  "
            + _("restaurant.current_total") + f": {balance.get('total', subtotal)}  |  "
            + _("restaurant.paid") + f": {balance.get('paid', '0')}  |  "
            + _("restaurant.remaining") + f": {balance.get('remaining', '0')}"
        )

    def add_menu_item(self, item):
        if not self.session:
            self.status.setText(_("restaurant.open_table_first"))
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_ADD_LINE):
            return
        try:
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
            self.load_session(self.session)
            self.status.setText(_("restaurant.line_added"))
        except Exception as exc:
            self.status.setText(str(exc))

    def add_line(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_ADD_LINE):
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
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_SEND_KITCHEN):
            return
        try:
            result = self.service.send_to_kitchen(int(self.session["id"]))
            tickets = (result or {}).get("tickets") or []
            try:
                settings = settings_service.get_restaurant_settings()
            except Exception:
                settings = {}
            if tickets and settings.get("operations", {}).get("auto_print_kitchen_ticket"):
                try:
                    restaurant_printing_bridge.kitchen_tickets_print(tickets, self)
                except Exception as print_exc:
                    self.status.setText(str(print_exc))
            self.load_session(self.session)
            self.status.setText(_("restaurant.kitchen_sent"))
            self.kitchenSent.emit(result or {})
        except Exception as exc:
            self.status.setText(str(exc))

    def print_last_kitchen_ticket(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET):
            return
        try:
            tickets = self.service.list_kitchen_tickets(status="all", limit=20)
            session_id = int(self.session.get("id"))
            ticket = next((t for t in tickets if int(t.get("session_id") or 0) == session_id), None)
            if not ticket:
                self.status.setText(_("restaurant.no_kitchen_ticket_to_print"))
                return
            if restaurant_printing_bridge.kitchen_ticket_print(int(ticket["id"]), self):
                self.status.setText(_("restaurant.kitchen_ticket_printed"))
        except Exception as exc:
            self.status.setText(str(exc))

    def _balance(self):
        if not self.session:
            return {"total": "0", "paid": "0", "remaining": "0"}
        try:
            return self.service.session_balance(int(self.session["id"]))
        except Exception:
            return {"total": "0", "paid": "0", "remaining": "0"}

    def adjust_bill(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_ADJUST_BILL):
            return
        try:
            balance = self._balance()
            dialog = RestaurantAdjustmentsDialog(balance, self)
            if dialog.exec() != QDialog.Accepted:
                return
            result = self.service.set_session_adjustments(session_id=int(self.session["id"]), **dialog.payload())
            self.load_session(self.session)
            self.status.setText(_("restaurant.adjustments_saved") + f" — {_('restaurant.current_total')}: {result.get('total', '0')}")
        except Exception as exc:
            self.status.setText(str(exc))

    def record_payment(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_RECORD_PAYMENT):
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

    def print_receipt(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_PRINT_RECEIPT):
            return
        try:
            if restaurant_printing_bridge.receipt_print(int(self.session["id"]), self):
                self.status.setText(_("restaurant.receipt_printed"))
        except Exception as exc:
            self.status.setText(str(exc))

    def checkout_session(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_CHECKOUT):
            return
        try:
            session_id = int(self.session["id"])
            result = self.service.checkout_session(session_id)
            reference = result.get("invoice_reference") or result.get("invoice_id") or ""
            try:
                settings = settings_service.get_restaurant_settings()
            except Exception:
                settings = {}
            if settings.get("operations", {}).get("auto_print_receipt_after_checkout"):
                try:
                    restaurant_printing_bridge.receipt_print(session_id, self)
                except Exception as print_exc:
                    self.status.setText(str(print_exc))
            self.status.setText(_("restaurant.checkout_done") + (f": {reference}" if reference else ""))
            self.session = None
            self.load_session(None)
            self.sessionClosed.emit()
        except Exception as exc:
            self.status.setText(str(exc))

    def close_session(self):
        # Backward-compatible alias for tests/plugins that still call the old slot.
        self.checkout_session()
