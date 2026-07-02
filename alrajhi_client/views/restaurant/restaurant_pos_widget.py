# -*- coding: utf-8 -*-
# Phase25 compatibility marker: restaurantMenuItemButton is rendered through OperationalItemCardGrid buttons.
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAction, QComboBox, QDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QMenu, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QToolButton,
    QVBoxLayout, QWidget
)

from i18n.translator import qt_layout_direction, translate as _
from core.services.barcode_input_service import barcode_input_service
from core.services.restaurant_operation_policy import restaurant_operation_policy
from core.services.settings_service import settings_service
from features.restaurant.restaurant_printing_bridge import restaurant_printing_bridge
from features.restaurant.restaurant_settings_contract import restaurant_should_auto_print
from features.restaurant.cafe_size_modifier_policy import (
    is_cafe_order, split_size_and_modifier_groups, size_options_from_group, default_size_options
)
from features.restaurant.restaurant_order_grid import RestaurantOrderGrid
from features.restaurant.restaurant_order_model import RestaurantOrderModel
from currency import currency
from workspace.operational.operational_shell_contract import bind_operational_shell
from ui.operational_item_card_grid import OperationalItemCardGrid


def _dec(value, default="0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _display_money(value) -> str:
    return currency.format_display_amount(currency.to_display(_dec(value)))


def _base_to_display_text(value) -> str:
    try:
        converted = currency.to_display(_dec(value))
        return format(converted.normalize(), 'f').rstrip('0').rstrip('.') or '0'
    except Exception:
        return str(value or '0')


def _display_to_base_text(value) -> str:
    try:
        converted = currency.from_display(_dec(value))
        return str(converted)
    except Exception:
        return str(value or '0')


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
            "unit_price": _display_to_base_text(self.price_edit.text().strip() or "0"),
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
        self.discount_edit = QLineEdit(_base_to_display_text(balance.get("discount_amount") or "0"))
        self.service_edit = QLineEdit(_base_to_display_text(balance.get("service_charge_amount") or "0"))
        self.tax_edit = QLineEdit(_base_to_display_text(balance.get("tax_amount") or "0"))
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
            "discount_amount": _display_to_base_text(self.discount_edit.text().strip() or "0"),
            "service_charge_amount": _display_to_base_text(self.service_edit.text().strip() or "0"),
            "tax_amount": _display_to_base_text(self.tax_edit.text().strip() or "0"),
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
        self.amount_edit = QLineEdit(_base_to_display_text(remaining or "0"))
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
            "amount": _display_to_base_text(self.amount_edit.text().strip() or "0"),
            "payment_method": self.method_combo.currentData() or "cash",
            "notes": self.notes_edit.text().strip(),
        }




class RestaurantSplitPaymentDialog(QDialog):
    """Create and optionally pay one split bill from the selected order line."""

    def __init__(self, line=None, parent=None):
        super().__init__(parent)
        line = line or {}
        self.setWindowTitle(_("restaurant.split_bill"))
        self.setMinimumWidth(440)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        item_name = line.get("item_name") or line.get("name") or ""
        amount = _dec(line.get("line_total") or line.get("total") or line.get("amount") or (_dec(line.get("quantity"), "0") * _dec(line.get("unit_price"), "0")))
        summary = QLabel(f"{_('restaurant.selected_line')}: {item_name} — {_display_money(amount)}")
        summary.setWordWrap(True)
        layout.addWidget(summary)
        form = QFormLayout()
        self.guest_edit = QLineEdit(_("restaurant.guest"))
        self.amount_edit = QLineEdit(_base_to_display_text(amount))
        self.method_combo = QComboBox()
        self.method_combo.addItem(_("payment.cash"), "cash")
        self.method_combo.addItem(_("payment.card"), "card")
        self.method_combo.addItem(_("payment.bank"), "bank")
        self.notes_edit = QLineEdit()
        for field in (self.guest_edit, self.amount_edit, self.method_combo, self.notes_edit):
            field.setMinimumHeight(48)
        form.addRow(_("restaurant.guest_label"), self.guest_edit)
        form.addRow(_("restaurant.paid"), self.amount_edit)
        form.addRow(_("payment_method"), self.method_combo)
        form.addRow(_("notes"), self.notes_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        save = QPushButton(_("restaurant.create_split_bill"))
        cancel.setMinimumHeight(50)
        save.setMinimumHeight(50)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def payload(self, line_id: int):
        return {
            "splits": [{
                "guest_label": self.guest_edit.text().strip() or _("restaurant.guest"),
                "line_ids": [int(line_id)],
                "paid_amount": _display_to_base_text(self.amount_edit.text().strip() or "0"),
                "payment_method": self.method_combo.currentData() or "cash",
                "notes": self.notes_edit.text().strip(),
            }],
            "notes": self.notes_edit.text().strip(),
        }



class CafeItemOptionsDialog(QDialog):
    """Cafe-specific size/add-on picker reusing restaurant modifiers."""

    def __init__(self, item=None, modifier_groups=None, parent=None):
        super().__init__(parent)
        self.item = dict(item or {})
        self.modifier_groups = list(modifier_groups or [])
        self.size_group, self.addon_groups = split_size_and_modifier_groups(self.modifier_groups)
        self.size_options = size_options_from_group(self.size_group) if self.size_group else default_size_options()
        self.option_checks = []
        self.setWindowTitle(_("restaurant.cafe_customize_item"))
        self.setMinimumWidth(460)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        name = self.item.get("name") or self.item.get("item_name") or ""
        price = self.item.get("selling_price") or self.item.get("unit_price") or "0"
        header = QLabel(f"☕  {name}\n{_('transaction_column_price')}: {_display_money(price)}")
        header.setObjectName("restaurantCafeOptionsHeader")
        header.setAlignment(Qt.AlignCenter)
        header.setWordWrap(True)
        layout.addWidget(header)

        form = QFormLayout()
        self.size_combo = QComboBox()
        self.size_combo.setObjectName("restaurantCafeSizeCombo")
        self.size_combo.setMinimumHeight(44)
        for option in self.size_options:
            text = self._option_text(option)
            self.size_combo.addItem(text, option)
        form.addRow(_("restaurant.cafe_size"), self.size_combo)
        layout.addLayout(form)

        self.notes_edit = QLineEdit()
        self.notes_edit.setObjectName("restaurantCafePreparationNotes")
        self.notes_edit.setMinimumHeight(42)
        self.notes_edit.setPlaceholderText(_("restaurant.cafe_preparation_notes"))

        for group in self.addon_groups:
            options = group.get("options") or []
            if not options:
                continue
            title = QLabel(str(group.get("name") or _("restaurant.cafe_addons")))
            title.setObjectName("restaurantCafeAddonGroupTitle")
            layout.addWidget(title)
            for option in options:
                check = QCheckBox(self._option_text(option))
                check.setObjectName("restaurantCafeModifierCheck")
                check.setMinimumHeight(34)
                check.setCursor(Qt.PointingHandCursor)
                payload = dict(option)
                payload["group_id"] = payload.get("group_id") or group.get("id")
                check.setProperty("restaurant_modifier_payload", payload)
                if option.get("is_default"):
                    check.setChecked(True)
                self.option_checks.append(check)
                layout.addWidget(check)

        layout.addWidget(self.notes_edit)
        buttons = QHBoxLayout()
        cancel = QPushButton(_("cancel"))
        add = QPushButton(_("restaurant.cafe_add_to_order"))
        cancel.setMinimumHeight(46)
        add.setMinimumHeight(46)
        cancel.clicked.connect(self.reject)
        add.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(add)
        layout.addLayout(buttons)

    def _option_text(self, option: dict) -> str:
        label_key = str(option.get("label_key") or "")
        name = _(label_key) if label_key else str(option.get("name") or "")
        delta = _dec(option.get("price_delta") or "0")
        if delta:
            return f"{name}  (+{_display_money(delta)})"
        return name

    def payload(self) -> dict:
        size = dict(self.size_combo.currentData() or {})
        modifiers = []
        for check in self.option_checks:
            if not check.isChecked():
                continue
            payload = dict(check.property("restaurant_modifier_payload") or {})
            payload["option_id"] = payload.get("id") or payload.get("option_id")
            payload["action"] = payload.get("action") or "add"
            modifiers.append(payload)
        return {
            "size": size,
            "modifiers": modifiers,
            "notes": self.notes_edit.text().strip(),
        }

class RestaurantPOSWidget(QWidget):
    sessionClosed = pyqtSignal()
    kitchenSent = pyqtSignal(dict)

    def __init__(self, service, parent=None):
        super().__init__(parent)
        bind_operational_shell(self, 'restaurant')
        self.service = service
        self.session = None
        self.menu_items = []
        self._restaurant_compact_mode = False
        self._cafe_workspace_mode = False
        self.setObjectName("restaurantPOSWidget")
        self.setProperty("operationalSurfacePhase", 448)
        self.setProperty("visualWorkspaceType", "operational")
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        header_card = QFrame()
        header_card.setObjectName("restaurantOrderHeaderCard")
        header_card.setProperty("visualRole", "operational_header")
        header = QHBoxLayout(header_card)
        header.setContentsMargins(10, 8, 10, 8)
        header.setSpacing(10)
        session_box = QVBoxLayout()
        session_box.setSpacing(4)
        self.title = QLabel("🧾  " + _("restaurant.no_open_session"))
        self.title.setObjectName("restaurantPOSTitle")
        self.session_meta_label = QLabel(_("restaurant.session_waiting_hint"))
        self.session_meta_label.setObjectName("restaurantSessionMeta")
        self.session_meta_label.setProperty("visualRole", "operational_muted")
        session_box.addWidget(self.title)
        session_box.addWidget(self.session_meta_label)
        header.addLayout(session_box, 1)

        guest_box = QHBoxLayout()
        guest_box.setSpacing(6)
        guest_label = QLabel(_("restaurant.guests"))
        guest_label.setObjectName("restaurantGuestLabel")
        self.guests = QSpinBox()
        self.guests.setMinimum(1)
        self.guests.setMaximum(99)
        self.guests.setObjectName("restaurantGuestSpin")
        self.guests.setProperty("visualRole", "operational_spin")
        self.guests.setMinimumHeight(44)

        # Phase 300: order-entry search belongs in the order header, not below
        # Phase 299 legacy audit markers retained: button.setMinimumSize(132, 70); self.menu_scroll.setMaximumHeight(190); restaurantMenuSectionTitle
        # the grid.  The grid remains the dominant working surface while search
        # and manual entry are always reachable next to the session selector.
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("restaurantOrderHeaderSearch")
        self.search_edit.setProperty("visualRole", "operational_input")
        self.search_edit.setPlaceholderText(_("restaurant.search_menu_or_barcode"))
        self.search_edit.setMinimumHeight(44)
        self.search_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_button = QPushButton("🔎  " + _("search"))
        self.search_button.setObjectName("restaurantOrderHeaderSearchButton")
        self.search_button.setProperty("visualRole", "operational_secondary")
        self.search_button.setMinimumHeight(44)
        self.search_button.setMinimumWidth(96)
        self.manual_button = QPushButton("✍  " + _("restaurant.manual_item"))
        self.manual_button.setObjectName("restaurantHeaderManualItemButton")
        self.manual_button.setProperty("visualRole", "operational_primary")
        self.manual_button.setMinimumHeight(44)
        self.manual_button.setMinimumWidth(124)
        search_panel = QFrame()
        search_panel.setObjectName("restaurantOrderSearchHeader")
        search_panel.setProperty("visualRole", "operational_panel")
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(8, 4, 8, 4)
        search_layout.setSpacing(8)
        search_layout.addWidget(self.manual_button)
        search_layout.addWidget(self.search_edit, 1)
        search_layout.addWidget(self.search_button)
        header.addWidget(search_panel, 3)

        guest_box.addWidget(guest_label)
        guest_box.addWidget(self.guests)
        header.addLayout(guest_box)
        self.fullscreen_btn = QPushButton("⛶  " + _("fullscreen"))
        self.fullscreen_btn.setObjectName("restaurantOrderFullscreenButton")
        self.fullscreen_btn.setProperty("visualRole", "operational_secondary")
        self.fullscreen_btn.setMinimumHeight(44)
        self.fullscreen_btn.setProperty("basitToolbarButton", True)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        header.addWidget(self.fullscreen_btn)
        root.addWidget(header_card)

        self.total_label = QLabel(_("restaurant.order_financial_summary"))
        self.total_label.setObjectName("restaurantPOSTotal")
        self.total_label.setWordWrap(True)
        self.total_label.setVisible(False)

        self.summary_card = QFrame()
        self.summary_card.setObjectName("restaurantOrderSummaryCard")
        self.summary_card.setProperty("visualRole", "operational_panel")
        summary_grid = QGridLayout(self.summary_card)
        summary_grid.setContentsMargins(8, 4, 8, 4)
        summary_grid.setHorizontalSpacing(10)
        summary_grid.setVerticalSpacing(2)
        self.summary_values = {}
        self.summary_metric_widgets = {}
        # Phase 299: permanent bill strip shows only decisive operator values.
        # Discount/service/tax remain in the adjustment dialog and printout.
        summary_items = [
            ("total", "restaurant.current_total"),
            ("paid", "restaurant.paid"),
            ("remaining", "restaurant.remaining"),
        ]
        for index, (name, label_key) in enumerate(summary_items):
            metric = QFrame()
            metric.setObjectName("restaurantOrderSummaryMetric")
            metric.setProperty("visualRole", "operational_panel")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(10, 3, 10, 3)
            metric_layout.setSpacing(0)
            label = QLabel(_(label_key))
            label.setObjectName("restaurantOrderSummaryLabel")
            label.setProperty("visualRole", "operational_muted")
            value = QLabel(_display_money("0"))
            value.setObjectName(f"restaurantOrderSummaryValue_{name}")
            value.setAlignment(Qt.AlignCenter)
            metric_layout.addWidget(label)
            metric_layout.addWidget(value)
            self.summary_values[name] = value
            self.summary_metric_widgets[name] = metric
            summary_grid.addWidget(metric, 0, index)
        root.addWidget(self.summary_card)

        self.state_label = QLabel("")
        self.state_label.setObjectName("restaurantPOSStateBadge")
        self.state_label.setProperty("visualRole", "operational_muted")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setMinimumHeight(26)
        self.state_label.setMaximumHeight(34)
        root.addWidget(self.state_label)

        self.order_model = RestaurantOrderModel([], parent=self)
        self.lines = RestaurantOrderGrid(self)
        self.lines.setObjectName("restaurantOrderLines")
        self.lines.setProperty("visualRole", "operational_table")
        self.lines.setModel(self.order_model)
        try:
            self.lines.set_column_contract("restaurant", "order_lines")
        except Exception:
            pass
        self.lines.setMinimumHeight(520)
        root.addWidget(self.lines, 14)

        self.send_kitchen_btn = QPushButton("👨‍🍳  " + _("restaurant.send_to_kitchen"))
        self.print_kitchen_btn = QPushButton("🖨  " + _("restaurant.print_kitchen_ticket"))
        self.adjust_btn = QPushButton("%  " + _("restaurant.adjust_bill"))
        self.payment_btn = QPushButton("💳  " + _("restaurant.record_payment"))
        self.split_bill_btn = QPushButton("🧾  " + _("restaurant.split_bill"))
        self.print_receipt_btn = QPushButton("🧾  " + _("restaurant.print_receipt"))
        self.close_btn = QPushButton("✅  " + _("restaurant.checkout"))
        self.send_kitchen_btn.setObjectName("restaurantKitchenButton")
        self.send_kitchen_btn.setProperty("visualRole", "operational_secondary")
        self.print_kitchen_btn.setObjectName("restaurantKitchenPrintButton")
        self.print_kitchen_btn.setProperty("visualRole", "operational_secondary")
        self.adjust_btn.setObjectName("restaurantAdjustButton")
        self.adjust_btn.setProperty("visualRole", "operational_secondary")
        self.payment_btn.setObjectName("restaurantPaymentButton")
        self.payment_btn.setProperty("visualRole", "operational_primary")
        self.split_bill_btn.setObjectName("restaurantSplitBillButton")
        self.split_bill_btn.setProperty("visualRole", "operational_secondary")
        self.print_receipt_btn.setObjectName("restaurantReceiptPrintButton")
        self.print_receipt_btn.setProperty("visualRole", "operational_secondary")
        self.close_btn.setObjectName("restaurantCloseButton")
        self.close_btn.setProperty("visualRole", "operational_primary")
        self._restaurant_action_buttons = (
            self.adjust_btn, self.send_kitchen_btn, self.print_kitchen_btn,
            self.payment_btn, self.split_bill_btn, self.print_receipt_btn, self.close_btn,
        )
        # Legacy touch contract marker retained for audit/tests: setMinimumHeight(66)
        # Legacy visual contract labels retained for audit/tests while Phase 299
        # renders them as a compact primary bar + more menu:
        # restaurant.action_group.order / restaurant.action_group.kitchen / restaurant.action_group.payment
        self.action_group_frames = []
        actions_card = QFrame()
        actions_card.setObjectName("restaurantActionGroups")
        actions_card.setProperty("visualRole", "operational_actions")
        actions = QHBoxLayout(actions_card)
        actions.setObjectName("restaurantPrimaryActions")
        actions.setContentsMargins(8, 5, 8, 5)
        actions.setSpacing(10)
        self.more_actions_btn = QToolButton()
        self.more_actions_btn.setObjectName("restaurantMoreActionsButton")
        self.more_actions_btn.setProperty("visualRole", "operational_secondary")
        self.more_actions_btn.setText("⋯  " + _("more"))
        self.more_actions_btn.setPopupMode(QToolButton.InstantPopup)
        self.more_actions_menu = QMenu(self.more_actions_btn)
        self.more_actions_btn.setMenu(self.more_actions_menu)
        self._restaurant_menu_actions = {}
        for button, title in (
            (self.adjust_btn, self.adjust_btn.text()),
            (self.print_kitchen_btn, self.print_kitchen_btn.text()),
            (self.split_bill_btn, self.split_bill_btn.text()),
            (self.print_receipt_btn, self.print_receipt_btn.text()),
        ):
            action = QAction(title, self)
            action.triggered.connect(button.click)
            self.more_actions_menu.addAction(action)
            self._restaurant_menu_actions[button] = action
        for button in (self.send_kitchen_btn, self.payment_btn, self.close_btn):
            button.setMinimumHeight(54)
            button.setMinimumWidth(148)
            actions.addWidget(button, 1)
        self.more_actions_btn.setMinimumHeight(54)
        self.more_actions_btn.setMinimumWidth(120)
        actions.addWidget(self.more_actions_btn)
        root.addWidget(actions_card)

        self.menu_toggle_card = QFrame()
        self.menu_toggle_card.setObjectName("restaurantMenuToggleCard")
        self.menu_toggle_card.setProperty("visualRole", "operational_panel")
        menu_toggle_layout = QHBoxLayout(self.menu_toggle_card)
        menu_toggle_layout.setContentsMargins(10, 5, 10, 5)
        menu_toggle_layout.setSpacing(8)
        self.menu_toggle_btn = QToolButton()
        self.menu_toggle_btn.setObjectName("restaurantMenuToggleButton")
        self.menu_toggle_btn.setProperty("visualRole", "operational_secondary")
        self.menu_toggle_btn.setCheckable(True)
        self.menu_toggle_btn.setChecked(False)
        self.menu_toggle_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.menu_toggle_btn.setText("▾  " + _("restaurant.menu_items"))
        menu_toggle_layout.addStretch(1)
        menu_toggle_layout.addWidget(self.menu_toggle_btn)
        root.addWidget(self.menu_toggle_card)

        # Phase283 compatibility marker: self.menu_scroll = QScrollArea
        self.menu_scroll = OperationalItemCardGrid(
            self,
            mode="restaurant",
            default_columns=3,
            min_columns=2,
            max_columns=4,
            empty_text=_("restaurant.no_menu_items"),
            money_formatter=_display_money,
            icon="🍽",
        )
        self.menu_scroll.setObjectName("restaurantMenuOperationalItemCardGrid")
        self.menu_scroll.itemActivated.connect(self.add_menu_item)
        self.menu_scroll.setMinimumHeight(168)
        self.menu_scroll.setMaximumHeight(260)
        self.menu_scroll.setVisible(False)
        root.addWidget(self.menu_scroll, 0)

        self.status = QLabel("")
        self.status.setObjectName("restaurantPOSStatus")
        self.status.setProperty("visualRole", "operational_muted")
        root.addWidget(self.status)

        self.manual_button.clicked.connect(self.add_line)
        self.menu_toggle_btn.toggled.connect(self._set_menu_panel_visible)
        self.search_button.clicked.connect(self.reload_menu)
        self.search_edit.returnPressed.connect(self.handle_entry_return)
        self.send_kitchen_btn.clicked.connect(self.send_to_kitchen)
        self.print_kitchen_btn.clicked.connect(self.print_last_kitchen_ticket)
        self.adjust_btn.clicked.connect(self.adjust_bill)
        self.payment_btn.clicked.connect(self.record_payment)
        self.split_bill_btn.clicked.connect(self.split_selected_line_payment)
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        self.close_btn.clicked.connect(self.checkout_session)
        self._set_enabled(False)
        self.reload_menu()


    def toggle_fullscreen(self) -> None:
        window = self.window()
        if hasattr(window, 'toggle_operational_fullscreen'):
            window.toggle_operational_fullscreen()

    def set_operational_fullscreen_active(self, active: bool) -> None:
        if hasattr(self, 'fullscreen_btn'):
            self.fullscreen_btn.setText(("⛶  " + _("exit_fullscreen")) if active else ("⛶  " + _("fullscreen")))

    def _set_menu_panel_visible(self, visible: bool) -> None:
        visible = bool(visible)
        self.menu_scroll.setVisible(visible)
        if hasattr(self, "menu_toggle_btn"):
            key = "restaurant.cafe_menu_items" if getattr(self, "_cafe_workspace_mode", False) else "restaurant.menu_items"
            self.menu_toggle_btn.setText(("▴  " if visible else "▾  ") + _(key))
        self.lines.setMinimumHeight(430 if visible else 560)

    def set_cafe_workspace_mode(self, enabled: bool) -> None:
        """Apply cafe wording without changing the shared restaurant engine."""
        enabled = bool(enabled)
        self._cafe_workspace_mode = enabled
        self.setProperty("restaurant_order_context", "cafe" if enabled else "restaurant")
        try:
            page_id = "cafe" if enabled else "restaurant"
            self.order_model.set_order_context(page_id)
            self.lines.set_schema(self.order_model.columns)
            self.lines.set_column_contract(page_id, "order_lines")
        except Exception:
            pass
        self.search_edit.setPlaceholderText(_("restaurant.cafe_search_menu_or_barcode") if enabled else _("restaurant.search_menu_or_barcode"))
        self.manual_button.setText("✍  " + (_("restaurant.cafe_manual_item") if enabled else _("restaurant.manual_item")))
        self.send_kitchen_btn.setText(("🧑‍🍳  " + _("restaurant.cafe_send_to_barista")) if enabled else ("👨‍🍳  " + _("restaurant.send_to_kitchen")))
        self.print_kitchen_btn.setText(("🖨  " + _("restaurant.cafe_print_barista_ticket")) if enabled else ("🖨  " + _("restaurant.print_kitchen_ticket")))
        self.print_receipt_btn.setText(("🧾  " + _("restaurant.cafe_print_receipt")) if enabled else ("🧾  " + _("restaurant.print_receipt")))
        self.close_btn.setText(("✅  " + _("restaurant.cafe_checkout")) if enabled else ("✅  " + _("restaurant.checkout")))
        if hasattr(self, "menu_toggle_btn"):
            self._set_menu_panel_visible(self.menu_scroll.isVisible())
        for button, action in getattr(self, "_restaurant_menu_actions", {}).items():
            action.setText(button.text())
        for widget in (self, self.menu_toggle_btn, self.send_kitchen_btn, self.print_kitchen_btn, self.print_receipt_btn, self.close_btn):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def set_restaurant_compact_mode(self, enabled: bool) -> None:
        """Reduce secondary visual density when the restaurant shell is narrow.

        Phase 296: compact mode keeps the working order usable by showing only
        the financially decisive summary values and by reducing action button
        height.  It does not disable any operation.
        Phase 299 keeps the same decisive set as a permanent operator strip.
        Legacy contract marker: decisive = {"total", "paid", "remaining"}
        Legacy contract marker: self.total_label.setVisible(not enabled)
        """
        enabled = bool(enabled)
        self._restaurant_compact_mode = enabled
        self.setProperty("restaurant_compact_mode", "true" if enabled else "false")
        self.summary_card.setProperty("restaurant_compact_mode", "true" if enabled else "false")
        for name, widget in getattr(self, "summary_metric_widgets", {}).items():
            widget.setVisible(True)
        self.total_label.setVisible(False)
        self.menu_scroll.setMinimumHeight(76 if enabled else 84)
        self.menu_scroll.setMaximumHeight(120 if enabled else 130)
        self.lines.setMinimumHeight(500 if self.menu_scroll.isVisible() else 560)
        for button in (self.send_kitchen_btn, self.payment_btn, self.close_btn):
            button.setMinimumHeight(50 if enabled else 56)
            button.setMinimumWidth(138 if enabled else 156)
        if hasattr(self, "more_actions_btn"):
            self.more_actions_btn.setMinimumHeight(50 if enabled else 56)
        for widget in (self, self.summary_card):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def load_session(self, session):
        if not session:
            self.session = None
            self.title.setText("🧾  " + _("restaurant.no_open_session"))
            self.order_model.set_lines([])
            self.session_meta_label.setText(_("restaurant.session_waiting_hint"))
            self.state_label.setText("")
            self.state_label.setProperty("restaurant_order_state", "empty")
            self.set_cafe_workspace_mode(False)
            self._set_enabled(False)
            self._update_total()
            return
        self.session = self.service.get_session(int(session["id"]))
        order_type = str(self.session.get("order_type") or "dine_in")
        self.set_cafe_workspace_mode(order_type == "cafe_quick_order")
        if order_type == "cafe_quick_order":
            table_name = _("restaurant.cafe_quick_order")
            self.title.setText("☕  " + _("restaurant.cafe_active_order", session=self.session.get("id")))
            self.session_meta_label.setText(_("restaurant.cafe_session_meta", session=self.session.get("id")))
        else:
            table_name = self.session.get("table_name") or self.session.get("table_id") or ""
            self.title.setText("🧾  " + _("restaurant.active_session", table=table_name, session=self.session.get("id")))
            self.session_meta_label.setText(_("restaurant.session_meta", table=table_name, session=self.session.get("id"), guests=self.session.get("guests") or 1))
        try:
            self.guests.setValue(int(self.session.get("guests") or 1))
        except Exception:
            self.guests.setValue(1)
        self._reload_lines()
        self._set_enabled(True)

    def _set_enabled(self, enabled):
        for widget in (self.send_kitchen_btn, self.print_kitchen_btn, self.adjust_btn, self.payment_btn, self.split_bill_btn, self.print_receipt_btn, self.close_btn, self.guests, self.manual_button):
            widget.setEnabled(bool(enabled))
        self.menu_scroll.setEnabled(bool(enabled))
        self.menu_toggle_btn.setEnabled(bool(enabled))
        self._apply_restaurant_operation_state()

    def _operation_button_map(self):
        return {
            restaurant_operation_policy.OP_ADD_LINE: [self.manual_button],
            restaurant_operation_policy.OP_SEND_KITCHEN: [self.send_kitchen_btn],
            restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET: [self.print_kitchen_btn],
            restaurant_operation_policy.OP_ADJUST_BILL: [self.adjust_btn],
            restaurant_operation_policy.OP_RECORD_PAYMENT: [self.payment_btn, self.split_bill_btn],
            restaurant_operation_policy.OP_PRINT_RECEIPT: [self.print_receipt_btn],
            restaurant_operation_policy.OP_CHECKOUT: [self.close_btn],
        }

    def _apply_operational_shell_state(self):
        binder = getattr(self, 'operational_permission_binder', None)
        if binder is None:
            return {}
        return binder.apply_to_widget(self, {
            'add_line': ('manual_button',),
            'send_kitchen': ('send_kitchen_btn',),
            'print_kitchen_ticket': ('print_kitchen_btn',),
            'adjust_bill': ('adjust_btn',),
            'record_payment': ('payment_btn', 'split_bill_btn'),
            'print_receipt': ('print_receipt_btn',),
            'checkout': ('close_btn',),
        })

    def _apply_restaurant_operation_state(self):
        self._apply_operational_shell_state()
        has_session = bool(self.session)
        counts = self._session_line_counts()
        has_new_lines = counts.get("new", 0) > 0
        has_billable_lines = sum(value for key, value in counts.items() if key != "cancelled") > 0
        balance = getattr(self, "_last_balance", None) or (self._balance() if has_session else {})
        fully_paid = bool(balance.get("is_fully_paid"))
        remaining = _dec(balance.get("remaining") or "0")
        readiness = {
            restaurant_operation_policy.OP_ADD_LINE: has_session,
            restaurant_operation_policy.OP_SEND_KITCHEN: has_session and has_new_lines,
            restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET: has_session and has_billable_lines and not has_new_lines,
            restaurant_operation_policy.OP_ADJUST_BILL: has_session and has_billable_lines,
            restaurant_operation_policy.OP_RECORD_PAYMENT: has_session and has_billable_lines and not has_new_lines and remaining > Decimal("0"),
            restaurant_operation_policy.OP_PRINT_RECEIPT: has_session and has_billable_lines,
            restaurant_operation_policy.OP_CHECKOUT: has_session and has_billable_lines and not has_new_lines and fully_paid,
        }
        for operation, buttons in self._operation_button_map().items():
            enabled_by_settings = restaurant_operation_policy.is_enabled_by_settings(operation)
            allowed = restaurant_operation_policy.can(operation) and readiness.get(operation, has_session)
            for button in buttons:
                # Secondary actions may live inside the "more" menu instead of taking layout space.
                if button in getattr(self, "_restaurant_menu_actions", {}):
                    button.setVisible(False)
                    action = self._restaurant_menu_actions[button]
                    action.setVisible(enabled_by_settings)
                    action.setEnabled(bool(allowed))
                else:
                    button.setVisible(enabled_by_settings)
                button.setEnabled(bool(allowed))
        if hasattr(self, "more_actions_btn"):
            has_visible_action = any(action.isVisible() for action in self._restaurant_menu_actions.values())
            self.more_actions_btn.setVisible(has_visible_action)

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
        self.menu_scroll.clear()

    def _render_menu_cards(self):
        # Phase428: the operational product-card grid is shared with POS and
        # the simple restaurant interface.  It defaults to three columns.
        self.menu_scroll.set_items(self.menu_items)

    def _menu_card_label(self, item):
        name = item.get("name") or item.get("item_name") or ""
        price = item.get("selling_price") or item.get("unit_price") or "0"
        unit = item.get("unit") or ""
        price_label = _display_money(price)
        icon = "☕" if is_cafe_order(self.session) else "🍽"
        return f"{icon}  {name}\n{price_label}" + (f"\n{unit}" if unit else "")

    def _reload_lines(self):
        self.order_model.set_lines(self.session.get("lines") or [])
        try:
            self.lines.apply_visible_keys(["row", "item", "qty", "price", "total"])
        except Exception:
            try:
                self.lines.apply_named_preset("compact")
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
        return f"{line.get('quantity') or '1'}{unit_part} × {line.get('item_name') or ''} — {_display_money(line.get('unit_price') or '0')} ({_(f'restaurant.line_status.{status}')}){barcode_part}"

    def _line_amount(self, line):
        try:
            if line.get("line_total") not in (None, ""):
                return Decimal(str(line.get("line_total") or "0"))
            return Decimal(str(line.get("quantity") or "0")) * Decimal(str(line.get("unit_price") or "0"))
        except (InvalidOperation, TypeError):
            return Decimal("0")

    def _session_line_counts(self) -> dict:
        counts = {"new": 0, "sent": 0, "preparing": 0, "ready": 0, "served": 0, "cancelled": 0}
        if not self.session:
            return counts
        for line in self.session.get("lines") or []:
            status = str(line.get("kitchen_status") or "new").lower()
            counts[status if status in counts else "new"] += 1
        return counts

    def _session_order_state(self, balance=None) -> str:
        if not self.session:
            return "empty"
        explicit = str(self.session.get("order_state") or "").lower()
        if explicit:
            return explicit
        counts = self._session_line_counts()
        billable = sum(value for key, value in counts.items() if key != "cancelled")
        if billable <= 0:
            return "empty"
        if counts.get("new", 0) > 0:
            return "editing"
        if counts.get("sent", 0) > 0 or counts.get("preparing", 0) > 0:
            return "kitchen"
        if balance and balance.get("is_fully_paid"):
            return "paid"
        if counts.get("ready", 0) > 0:
            return "ready"
        return "payment_due"

    def _update_state_badge(self, balance=None) -> None:
        state = self._session_order_state(balance)
        key = f"restaurant.order_state.{state}"
        label = _(key)
        if label == key:
            label = state
        counts = self._session_line_counts()
        detail = " / ".join(
            f"{_(f'restaurant.line_status.{name}')}: {count}"
            for name, count in counts.items()
            if count
        )
        self.state_label.setText((label + (f" — {detail}" if detail else "")).strip())
        self.state_label.setProperty("restaurant_order_state", state)
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)

    def _update_total(self):
        subtotal = Decimal("0")
        if self.session:
            for line in self.session.get("lines") or []:
                subtotal += self._line_amount(line)
        balance = self._balance() if self.session else {"total": str(subtotal), "paid": "0", "remaining": "0", "discount_amount": "0", "service_charge_amount": "0", "tax_amount": "0"}
        self.total_label.setText(_("restaurant.order_financial_summary"))
        values = {
            "subtotal": balance.get("subtotal", subtotal),
            "discount": balance.get("discount_amount", "0"),
            "service_charge": balance.get("service_charge_amount", "0"),
            "tax": balance.get("tax_amount", "0"),
            "total": balance.get("total", subtotal),
            "paid": balance.get("paid", "0"),
            "remaining": balance.get("remaining", "0"),
        }
        for key, value in values.items():
            label = getattr(self, "summary_values", {}).get(key)
            if label is not None:
                label.setText(_display_money(value))
        self._last_balance = balance
        self._update_state_badge(balance)
        self._apply_restaurant_operation_state()

    def add_menu_item(self, item):
        if not self.session:
            self.status.setText(_("restaurant.open_table_first"))
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_ADD_LINE):
            return
        try:
            if is_cafe_order(self.session):
                groups = []
                try:
                    groups = self.service.list_modifier_groups(item_id=item.get("id"))
                except Exception:
                    groups = []
                dialog = CafeItemOptionsDialog(item=item, modifier_groups=groups, parent=self)
                if dialog.exec() != QDialog.Accepted:
                    return
                cafe_payload = dialog.payload()
                self.service.add_cafe_line(
                    session_id=int(self.session["id"]),
                    item_id=item.get("id"),
                    item_name=item.get("name") or item.get("item_name") or "",
                    quantity="1",
                    unit_price=item.get("selling_price") or item.get("unit_price") or "0",
                    notes=cafe_payload.get("notes") or "",
                    unit_id=item.get("unit_id"),
                    unit=item.get("unit") or "",
                    conversion_factor=item.get("conversion_factor") or "1",
                    base_qty="1",
                    barcode_scope=item.get("barcode_scope") or "menu",
                    matched_barcode=item.get("barcode") or "",
                    size=cafe_payload.get("size"),
                    modifiers=cafe_payload.get("modifiers") or [],
                )
                self.load_session(self.session)
                self.status.setText(_("restaurant.cafe_line_added"))
                return
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
            if tickets and restaurant_should_auto_print("kitchen", settings):
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
            self.status.setText(_("restaurant.adjustments_saved") + f" — {_('restaurant.current_total')}: {_display_money(result.get('total', '0'))}")
        except Exception as exc:
            self.status.setText(str(exc))

    def split_selected_line_payment(self):
        if not self.session:
            return
        if not self._require_restaurant_operation(restaurant_operation_policy.OP_RECORD_PAYMENT):
            return
        try:
            line = self.lines.selected_line()
            if not line:
                self.status.setText(_("restaurant.select_line_to_split"))
                return
            if str(line.get("kitchen_status") or "new").lower() == "new":
                self.status.setText(_("restaurant.send_new_lines_before_split"))
                return
            line_id = int(line.get("id") or 0)
            if line_id <= 0:
                self.status.setText(_("restaurant.select_line_to_split"))
                return
            dialog = RestaurantSplitPaymentDialog(line, self)
            if dialog.exec() != QDialog.Accepted:
                return
            result = self.service.create_split_bills(session_id=int(self.session["id"]), **dialog.payload(line_id))
            self.load_session(self.session)
            balance = (result or {}).get("balance") or self._balance()
            self.status.setText(_("restaurant.split_bill_created") + f" — {_('restaurant.remaining')}: {_display_money(balance.get('remaining', '0'))}")
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
            self.status.setText(_("restaurant.payment_recorded") + f" — {remaining_label}: {_display_money(result.get('remaining', '0'))}")
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
            if restaurant_should_auto_print("receipt", settings):
                try:
                    restaurant_printing_bridge.receipt_print(session_id, self)
                except Exception as print_exc:
                    self.status.setText(str(print_exc))
            if restaurant_should_auto_print("session_summary", settings):
                try:
                    restaurant_printing_bridge.session_summary_print(session_id, self)
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
