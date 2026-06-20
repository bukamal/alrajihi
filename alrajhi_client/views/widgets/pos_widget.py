# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox, QDoubleSpinBox, QShortcut, QInputDialog, QMenu
)
import qtawesome as qta

from core.services.pos_service import pos_service, POSException
from core.services.warehouse_service import warehouse_service
from core.services.cashbox_service import cashbox_service
from core.services.settings_service import settings_service
from core.services.permission_service import permission_service
from currency import currency
from utils import show_toast
from views.widgets.modern_ui import apply_modern_widget
from theme_manager import ThemeManager
from features.pos.pos_preferences import POSPreferences
from features.pos.pos_line_grid import POSLineGrid
from features.pos.pos_line_model import POSLineModel
from features.pos.pos_payment_shell import POSPaymentShell
from core.services.pos_operation_policy import pos_operation_policy
from features.pos.pos_line_schema import pos_line_schema
from workspace.operational.operational_shell_contract import bind_operational_shell
from features.transactions.grids.transaction_column_presets import (
    preset_names, preset_title, visible_keys_for_preset,
)
from i18n import translate, qt_layout_direction


class POSWidget(QWidget):
    """Fast barcode sale screen for cashier-style workflows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction(settings_service.get_language()))
        bind_operational_shell(self, 'pos')
        self._pos_settings = settings_service.get_pos_settings()
        self._pos_preferences = POSPreferences()
        self.cart = pos_service.new_cart(self._selected_warehouse_id() if hasattr(self, 'warehouse_combo') else None, self._selected_cashbox_id() if hasattr(self, 'cashbox_combo') else None)
        self.display_curr = currency.get_display_currency()
        self._pos_columns = self._build_pos_columns()
        self._visible_pos_columns = self._load_visible_pos_columns()
        self._preset = self._pos_preferences.preset(str(self._pos_settings.get('default_line_preset') or 'cashier'))
        self._density = self._pos_preferences.density(str(self._pos_settings.get('touch_density') or 'touch'))
        self._init_ui()
        # Phase117: keep POS compact; page title is already represented by navigation/context.
        apply_modern_widget(self)
        self._setup_shortcuts()
        self._apply_touch_density()
        self._apply_pos_permissions()
        self._apply_operational_shell_state()
        self.refresh_cart()

    def _focus_barcode_input(self):
        """Safely focus the barcode field when the POS UI has been fully built.

        In remote/client mode a REST endpoint may fail while the POS page is still
        being initialized. Qt can still deliver show/focus events to the partial
        widget; direct access to self.barcode_input then raises AttributeError and
        aborts the whole application. This guard keeps page-load failures isolated.
        """
        widget = getattr(self, 'barcode_input', None)
        if widget is not None:
            try:
                widget.setFocus()
            except RuntimeError:
                pass

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.addStretch()
        self.columns_btn = QPushButton(translate("pos_columns_btn"))
        self._build_columns_menu()
        title_row.addWidget(self.columns_btn)

        self.preset_combo = QComboBox()
        for preset in preset_names():
            self.preset_combo.addItem(preset_title(preset), preset)
        preset_idx = self.preset_combo.findData(self._preset)
        if preset_idx >= 0:
            self.preset_combo.setCurrentIndex(preset_idx)
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        title_row.addWidget(QLabel(translate('transaction_preset')))
        title_row.addWidget(self.preset_combo)

        self.density_combo = QComboBox()
        self.density_combo.addItem(translate('pos_density_compact'), 'compact')
        self.density_combo.addItem(translate('pos_density_comfortable'), 'comfortable')
        self.density_combo.addItem(translate('pos_density_touch'), 'touch')
        idx = self.density_combo.findData(self._density)
        if idx >= 0:
            self.density_combo.setCurrentIndex(idx)
        self.density_combo.currentIndexChanged.connect(self.on_density_changed)
        title_row.addWidget(QLabel(translate('pos_density')))
        title_row.addWidget(self.density_combo)

        self.fullscreen_btn = QPushButton(translate("fullscreen"))
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        title_row.addWidget(self.fullscreen_btn)
        layout.addLayout(title_row)

        hint = QLabel(translate("pos_hint_shortcuts"))
        hint.setObjectName("muted")
        layout.addWidget(hint)

        wh_row = QHBoxLayout()
        wh_row.addWidget(QLabel(translate("issue_warehouse")))
        self.warehouse_combo = QComboBox()
        self._load_warehouses()
        self.warehouse_combo.currentIndexChanged.connect(self.on_warehouse_changed)
        wh_row.addWidget(self.warehouse_combo, 1)
        layout.addLayout(wh_row)

        shift_row = QHBoxLayout()
        shift_row.addWidget(QLabel(translate("cashbox")))
        self.cashbox_combo = QComboBox()
        self._load_cashboxes()
        self.cashbox_combo.currentIndexChanged.connect(self.on_cashbox_changed)
        shift_row.addWidget(self.cashbox_combo, 1)
        self.shift_label = QLabel(translate("no_open_shift"))
        self.shift_label.setObjectName("muted")
        shift_row.addWidget(self.shift_label, 1)
        self.open_shift_btn = QPushButton(translate("open_shift"))
        self.open_shift_btn.clicked.connect(self.open_shift)
        self.close_shift_btn = QPushButton(translate("close_shift"))
        self.close_shift_btn.clicked.connect(self.close_shift)
        shift_row.addWidget(self.open_shift_btn)
        shift_row.addWidget(self.close_shift_btn)
        layout.addLayout(shift_row)
        self._shift_row_widgets = [self.shift_label, self.open_shift_btn, self.close_shift_btn]
        self._apply_shift_mode_visibility()

        scan_row = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText(translate("pos_barcode_placeholder"))
        self.barcode_input.setMinimumHeight(60)
        self.barcode_input.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.barcode_input.returnPressed.connect(self.scan_entered_barcode)
        scan_row.addWidget(self.barcode_input, 1)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.001, 999999)
        self.qty_spin.setDecimals(int(self._pos_settings.get('quantity_decimals', 3) or 3))
        self.qty_spin.setValue(1)
        self.qty_spin.setPrefix(translate("qty_prefix"))
        scan_row.addWidget(self.qty_spin)

        camera_btn = QPushButton(translate("camera_scan"))
        camera_btn.clicked.connect(self.scan_with_camera)
        scan_row.addWidget(camera_btn)
        layout.addLayout(scan_row)

        self.table = POSLineGrid(self, identity='pos.lines')
        self.table_model = POSLineModel(self.cart, self.display_curr, self)
        self.table.setModel(self.table_model)
        self.table.apply_visible_keys(self._visible_pos_columns)
        self.table.apply_density(self._density)
        layout.addWidget(self.table, 1)

        self.payment_shell = POSPaymentShell(self, self)
        layout.addWidget(self.payment_shell)

        # Backward-compatible aliases used by the existing POS workflow.
        self.total_label = self.payment_shell.total_label
        self.change_label = self.payment_shell.change_label
        self.payment_combo = self.payment_shell.payment_combo
        self.paid_spin = self.payment_shell.paid_spin
        self.cash_btn = self.payment_shell.cash_btn
        self.card_btn = self.payment_shell.card_btn
        self.suspend_btn = self.payment_shell.suspend_btn
        self.resume_btn = self.payment_shell.resume_btn
        self.remove_btn = self.payment_shell.remove_btn
        self.clear_btn = self.payment_shell.clear_btn
        self.checkout_btn = self.payment_shell.checkout_btn

        default_payment = self._pos_settings.get('default_payment_method', 'cash')
        payment_index = self.payment_combo.findData(default_payment)
        if payment_index >= 0:
            self.payment_combo.setCurrentIndex(payment_index)
        self.payment_combo.currentIndexChanged.connect(self.on_payment_method_changed)
        self.paid_spin.valueChanged.connect(self.update_change_due)

        self.cash_btn.clicked.connect(self.pay_cash_full)
        self.card_btn.clicked.connect(self.pay_card_full)
        self.suspend_btn.clicked.connect(self.suspend_cart)
        self.resume_btn.clicked.connect(self.resume_cart)
        self.remove_btn.clicked.connect(self.remove_selected_line)
        self.clear_btn.clicked.connect(self.clear_cart)
        self.checkout_btn.clicked.connect(self.checkout)

        self.status_label = QLabel(translate("ready_to_scan"))
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)



    def _build_pos_columns(self):
        return pos_line_schema()

    def _load_visible_pos_columns(self):
        default = list(visible_keys_for_preset(getattr(self, '_preset', 'cashier'), self._pos_columns))
        return self._pos_preferences.visible_columns(default)

    def _save_visible_pos_columns(self):
        self._pos_preferences.save_visible_columns(self._visible_pos_columns)

    def _build_columns_menu(self):
        menu = QMenu(self.columns_btn)
        self._column_actions = {}
        for col in self._pos_columns:
            action = menu.addAction(col.title)
            action.setCheckable(True)
            action.setChecked(col.key in self._visible_pos_columns)
            action.toggled.connect(lambda checked, key=col.key: self._set_pos_column_visible(key, checked))
            self._column_actions[col.key] = action
        menu.addSeparator()
        menu.addAction(translate('reset_columns'), self._reset_pos_columns)
        self.columns_btn.setMenu(menu)

    def _set_pos_column_visible(self, key, visible):
        if visible and key not in self._visible_pos_columns:
            self._visible_pos_columns.append(key)
        elif not visible and key in self._visible_pos_columns:
            if len(self._visible_pos_columns) <= 1 or key in {col.key for col in self._pos_columns if col.required}:
                action = getattr(self, '_column_actions', {}).get(key)
                if action is not None and not action.isChecked():
                    action.blockSignals(True)
                    action.setChecked(True)
                    action.blockSignals(False)
                return
            self._visible_pos_columns.remove(key)
        self._save_visible_pos_columns()
        self._apply_pos_column_visibility()

    def _reset_pos_columns(self):
        self._visible_pos_columns = list(visible_keys_for_preset(getattr(self, '_preset', 'cashier'), self._pos_columns))
        visible = set(self._visible_pos_columns)
        for key, action in getattr(self, '_column_actions', {}).items():
            action.blockSignals(True)
            action.setChecked(key in visible)
            action.blockSignals(False)
        self._save_visible_pos_columns()
        self._apply_pos_column_visibility()

    def _apply_pos_column_visibility(self):
        table = getattr(self, 'table', None)
        if table is None:
            return
        visible = set(self._visible_pos_columns)
        table.apply_visible_keys([col.key for col in self._pos_columns if col.key in visible])

    def _pos_shifts_enabled(self):
        try:
            return bool(settings_service.get_pos_settings().get('use_shifts'))
        except Exception:
            return False

    def _apply_shift_mode_visibility(self):
        enabled = self._pos_shifts_enabled()
        for widget in getattr(self, '_shift_row_widgets', []):
            widget.setVisible(enabled)
        if hasattr(self, 'shift_label') and not enabled:
            self.shift_label.setText(translate('shifts_disabled_direct_cashbox'))

    def _load_cashboxes(self):
        self.cashbox_combo.clear()
        try:
            default_id = self._pos_settings.get('default_cashbox_id') or cashbox_service.default_cashbox_id()
            for cb in cashbox_service.cashboxes():
                self.cashbox_combo.addItem(cb.get('name', f"#{cb.get('id')}"), cb.get('id'))
                if default_id and int(cb.get('id')) == int(default_id):
                    self.cashbox_combo.setCurrentIndex(self.cashbox_combo.count() - 1)
        except Exception:
            pass
        self.refresh_shift_state()

    def _selected_cashbox_id(self):
        try:
            return int(self.cashbox_combo.currentData() or 0) or None
        except Exception:
            return None

    def refresh_shift_state(self):
        try:
            if not self._pos_shifts_enabled():
                self.current_shift_id = None
                if hasattr(self, 'shift_label'):
                    self.shift_label.setText(translate('shifts_disabled_direct_cashbox_short'))
                if hasattr(self, 'open_shift_btn'):
                    self.open_shift_btn.setEnabled(False)
                if hasattr(self, 'close_shift_btn'):
                    self.close_shift_btn.setEnabled(False)
                if hasattr(self, 'checkout_btn'):
                    self.checkout_btn.setEnabled(bool(getattr(self, 'cart', None) and self.cart.lines) and pos_operation_policy.can(pos_operation_policy.OP_CHECKOUT))
                return

            shift = cashbox_service.current_open_shift(self._selected_cashbox_id())
            if shift:
                self.current_shift_id = shift.get('id')
                self.shift_label.setText(translate("open_shift_label", id=shift.get('id'), cashbox=shift.get('cashbox_name','')))
                self.open_shift_btn.setEnabled(False)
                self.close_shift_btn.setEnabled(True)
            else:
                self.current_shift_id = None
                self.shift_label.setText(translate('no_open_shift'))
                self.open_shift_btn.setEnabled(True)
                self.close_shift_btn.setEnabled(False)
            if hasattr(self, 'checkout_btn'):
                self.checkout_btn.setEnabled(
                    bool(getattr(self, 'cart', None) and self.cart.lines)
                    and bool(getattr(self, 'current_shift_id', None))
                    and pos_operation_policy.can(pos_operation_policy.OP_CHECKOUT)
                )
        except Exception:
            pass

    def on_cashbox_changed(self):
        if getattr(self, 'cart', None) and self.cart.lines:
            reply = QMessageBox.question(self, translate("change_cashbox"), translate("change_cashbox_clear_cart_confirm"), QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.cart = pos_service.new_cart(self._selected_warehouse_id(), self._selected_cashbox_id())
        self.refresh_cart()
        self.refresh_shift_state()
        self._focus_barcode_input()

    def open_shift(self):
        if not self._pos_shifts_enabled():
            show_toast(translate('shifts_disabled_direct_cashbox'), "info", self)
            self._focus_barcode_input()
            return
        if not self._require_pos_operation(pos_operation_policy.OP_OPEN_SHIFT):
            return
        cashbox_id = self._selected_cashbox_id()
        if not cashbox_id:
            QMessageBox.warning(self, translate("shift"), translate("select_cashbox_first"))
            return
        opening, ok = QInputDialog.getDouble(self, translate("open_shift"), translate("opening_balance"), 0, 0, 999999999, 2)
        if not ok:
            return
        try:
            sid = cashbox_service.open_shift({'cashbox_id': cashbox_id, 'opening_amount': Decimal(str(opening))})
            self.cart = pos_service.new_cart(self._selected_warehouse_id(), cashbox_id, sid)
            self.refresh_shift_state()
            show_toast(translate("shift_opened"), "success", self)
        except Exception as e:
            QMessageBox.warning(self, translate("error"), str(e))
        self._focus_barcode_input()

    def close_shift(self):
        if not self._pos_shifts_enabled():
            show_toast(translate('shifts_disabled_direct_cashbox'), "info", self)
            self._focus_barcode_input()
            return
        if not self._require_pos_operation(pos_operation_policy.OP_CLOSE_SHIFT):
            return
        shift = cashbox_service.current_open_shift(self._selected_cashbox_id())
        if not shift:
            QMessageBox.information(self, translate("close_shift"), translate("no_open_shift"))
            return
        try:
            summary = cashbox_service.shift_summary(shift['id'])
            expected = Decimal(str(summary.get('expected_amount') or 0))
        except Exception:
            expected = Decimal('0')
        actual, ok = QInputDialog.getDouble(self, translate("close_shift"), translate("expected_actual_balance", expected=currency.format_amount(currency.convert(expected, currency.storage_currency(), self.display_curr))), float(currency.convert(expected, currency.storage_currency(), self.display_curr)), 0, 999999999, 2)
        if not ok:
            return
        try:
            actual_usd = currency.convert(Decimal(str(actual)), self.display_curr, currency.storage_currency())
            summary = cashbox_service.close_shift(shift['id'], actual_usd)
            diff = Decimal(str(summary.get('difference_amount') or 0))
            QMessageBox.information(self, translate("shift_close_report"), translate("shift_closed_report_msg", id=shift['id'], sales=summary.get('total_sales'), cash=summary.get('total_cash'), card=summary.get('total_card'), diff=diff))
            self.cart = pos_service.new_cart(self._selected_warehouse_id(), self._selected_cashbox_id())
            self.refresh_shift_state()
            self.refresh_cart()
        except Exception as e:
            QMessageBox.warning(self, translate("error"), str(e))
        self._focus_barcode_input()

    def _load_warehouses(self):
        self.warehouse_combo.clear()
        try:
            default_id = self._pos_settings.get('default_warehouse_id') or warehouse_service.default_warehouse_id()
            for wh in warehouse_service.warehouses():
                self.warehouse_combo.addItem(wh.get('name', f"#{wh.get('id')}"), wh.get('id'))
                if default_id and int(wh.get('id')) == int(default_id):
                    self.warehouse_combo.setCurrentIndex(self.warehouse_combo.count() - 1)
        except Exception:
            pass

    def _selected_warehouse_id(self):
        try:
            return int(self.warehouse_combo.currentData() or 0) or None
        except Exception:
            return None

    def on_warehouse_changed(self):
        new_id = self._selected_warehouse_id()
        if self.cart.lines:
            reply = QMessageBox.question(self, translate("change_warehouse"), translate("change_warehouse_clear_cart_confirm"), QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.cart = pos_service.new_cart(new_id, self._selected_cashbox_id())
        self.refresh_cart()
        self._focus_barcode_input()

    def on_density_changed(self):
        value = self.density_combo.currentData() or 'touch'
        self._density = str(value)
        self._pos_preferences.save_density(self._density)
        self._apply_touch_density()
        self._focus_barcode_input()

    def on_preset_changed(self):
        value = self.preset_combo.currentData() or 'cashier'
        self._preset = str(value)
        self._pos_preferences.save_preset(self._preset)
        keys = list(visible_keys_for_preset(self._preset, self._pos_columns))
        self._visible_pos_columns = keys
        self._save_visible_pos_columns()
        for key, action in getattr(self, '_column_actions', {}).items():
            action.blockSignals(True)
            action.setChecked(key in keys)
            action.blockSignals(False)
        self._apply_pos_column_visibility()
        self._focus_barcode_input()

    def _apply_touch_density(self):
        density = getattr(self, '_density', 'touch') or 'touch'
        if density == 'compact':
            input_h, row_h, font_px, button_h = 42, 32, 18, 36
        elif density == 'comfortable':
            input_h, row_h, font_px, button_h = 52, 40, 21, 44
        else:
            input_h, row_h, font_px, button_h = 68, 54, 26, 56
        if hasattr(self, 'barcode_input'):
            self.barcode_input.setMinimumHeight(input_h)
            self.barcode_input.setStyleSheet(f"font-size: {font_px}px; font-weight: bold; padding: 8px;")
        if hasattr(self, 'qty_spin'):
            self.qty_spin.setMinimumHeight(input_h)
        if hasattr(self, 'table'):
            try:
                self.table.apply_density(density)
            except Exception:
                self.table.verticalHeader().setDefaultSectionSize(row_h)
        if hasattr(self, 'payment_shell'):
            try:
                self.payment_shell.apply_density(density)
            except Exception:
                pass
        for btn_name in ('fullscreen_btn', 'columns_btn'):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setMinimumHeight(button_h)

    def _apply_pos_permissions(self):
        try:
            allowed = permission_service.can(permission_service.ACTION_USE_POS)
        except Exception:
            allowed = True
        if not allowed:
            self.setEnabled(False)
            try:
                show_toast(permission_service.denied_message(permission_service.ACTION_USE_POS), "warning", self)
            except Exception:
                pass
            return
        self._apply_pos_operation_state()

    def _apply_operational_shell_state(self):
        binder = getattr(self, 'operational_permission_binder', None)
        if binder is None:
            return {}
        return binder.apply_to_widget(self, {
            'suspend': ('suspend_btn',),
            'resume': ('resume_btn',),
            'remove_line': ('remove_btn',),
            'clear_cart': ('clear_btn',),
            'checkout': ('checkout_btn',),
            'open_shift': ('open_shift_btn',),
            'close_shift': ('close_shift_btn',),
        })

    def _apply_pos_operation_state(self):
        self._apply_operational_shell_state()
        mapping = {
            'suspend_btn': pos_operation_policy.OP_SUSPEND,
            'resume_btn': pos_operation_policy.OP_RESUME,
            'remove_btn': pos_operation_policy.OP_REMOVE_LINE,
            'clear_btn': pos_operation_policy.OP_CLEAR_CART,
            'checkout_btn': pos_operation_policy.OP_CHECKOUT,
            'open_shift_btn': pos_operation_policy.OP_OPEN_SHIFT,
            'close_shift_btn': pos_operation_policy.OP_CLOSE_SHIFT,
        }
        shifts_enabled = self._pos_shifts_enabled()
        for attr, operation in mapping.items():
            widget = getattr(self, attr, None)
            if widget is not None:
                try:
                    visible = pos_operation_policy.can(operation)
                    if operation in (pos_operation_policy.OP_OPEN_SHIFT, pos_operation_policy.OP_CLOSE_SHIFT):
                        visible = visible and shifts_enabled
                    widget.setVisible(visible)
                except Exception:
                    pass

    def _require_pos_operation(self, operation: str) -> bool:
        try:
            pos_operation_policy.require(operation)
            pos_operation_policy.log(operation, allowed=True)
            return True
        except PermissionError as exc:
            try:
                pos_operation_policy.log(operation, allowed=False, context=str(exc))
            except Exception:
                pass
            show_toast(str(exc), "warning", self)
            self._focus_barcode_input()
            return False

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F2"), self, self.pay_cash_full)
        QShortcut(QKeySequence("F3"), self, self.pay_card_full)
        QShortcut(QKeySequence("F4"), self, self.suspend_cart)
        QShortcut(QKeySequence("F5"), self, self.resume_cart)
        QShortcut(QKeySequence("F10"), self, self.checkout)
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_line)
        QShortcut(QKeySequence("Escape"), self, self.clear_cart)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self._focus_barcode_input())
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)

    def scan_entered_barcode(self):
        code = self.barcode_input.text().strip()
        self.add_barcode_to_cart(code, mode='auto')

    def set_global_filter(self, text: str):
        # In POS the context search acts as the cashier scan/search field.
        if hasattr(self, 'barcode_input'):
            self.barcode_input.setText(text or '')
            self._focus_barcode_input()

    def scan_with_camera(self):
        try:
            from views.dialogs.barcode_camera_dialog import BarcodeCameraDialog
            dialog = BarcodeCameraDialog(self)
            dialog.barcode_scanned.connect(lambda value, sym=None: self.add_barcode_to_cart(value, mode='scan'))
            dialog.exec()
        except Exception as e:
            show_toast(translate("camera_start_failed", error=e), "warning", self)
            self._focus_barcode_input()

    def add_barcode_to_cart(self, code, mode='auto'):
        try:
            line = pos_service.add_scan(self.cart, code, Decimal(str(self.qty_spin.value())), mode=mode)
            self.status_label.setText(translate("item_added_updated", item=line.name))
            self.barcode_input.clear()
            self.qty_spin.setValue(1)
            self.refresh_cart()
            show_toast(translate("item_added"), "success", self)
        except POSException as e:
            show_toast(str(e), "error", self)
        except Exception as e:
            show_toast(translate("scan_error", error=e), "error", self)
        finally:
            self._focus_barcode_input()

    def refresh_cart(self):
        if hasattr(self, 'table_model'):
            self.table_model.set_display_currency(self.display_curr)
            self.table_model.set_cart(self.cart)
        total_display = currency.convert(self.cart.total_usd, currency.storage_currency(), self.display_curr)
        self.total_label.setText(translate("total_amount", amount=currency.format_amount(total_display)))
        if self.payment_combo.currentData() in ('cash', 'card'):
            self.paid_spin.setValue(float(total_display))
        self.update_change_due()
        self.refresh_shift_state()
        self._apply_pos_operation_state()
        self.checkout_btn.setEnabled(
            bool(self.cart.lines)
            and pos_operation_policy.can(pos_operation_policy.OP_CHECKOUT)
            and (not self._pos_shifts_enabled() or bool(getattr(self, 'current_shift_id', None)))
        )

    def update_change_due(self):
        try:
            paid_display = Decimal(str(self.paid_spin.value()))
            total_display = currency.convert(self.cart.total_usd, currency.storage_currency(), self.display_curr)
            change = paid_display - total_display
            if change > 0:
                self.change_label.setText(translate("change_due_customer", amount=currency.format_amount(change)))
                self.change_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeManager.get('success')};")
            elif change < 0:
                self.change_label.setText(translate("remaining_amount", amount=currency.format_amount(abs(change))))
                self.change_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeManager.get('danger')};")
            else:
                self.change_label.setText(translate("change_zero"))
                self.change_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeManager.get('success')};")
        except Exception:
            pass

    def toggle_fullscreen(self):
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
            self.fullscreen_btn.setText(translate("fullscreen"))
        else:
            window.showFullScreen()
            self.fullscreen_btn.setText(translate("exit_fullscreen"))
        self._focus_barcode_input()

    def on_payment_method_changed(self):
        if self.payment_combo.currentData() == 'credit':
            self.paid_spin.setValue(0)
        else:
            total_display = currency.convert(self.cart.total_usd, currency.storage_currency(), self.display_curr)
            self.paid_spin.setValue(float(total_display))

    def pay_cash_full(self):
        self.payment_combo.setCurrentIndex(0)
        self.on_payment_method_changed()

    def pay_card_full(self):
        self.payment_combo.setCurrentIndex(1)
        self.on_payment_method_changed()

    def remove_selected_line(self):
        if not self._require_pos_operation(pos_operation_policy.OP_REMOVE_LINE):
            return
        row = self.table.selected_row()
        if row < 0 or row >= len(self.cart.lines):
            return
        pos_service.remove_line_at(self.cart, row)
        self.refresh_cart()
        self._focus_barcode_input()

    def clear_cart(self):
        if not self._require_pos_operation(pos_operation_policy.OP_CLEAR_CART):
            return
        if not self.cart.lines:
            self._focus_barcode_input()
            return
        reply = QMessageBox.question(self, translate("cancel_sale"), translate("cancel_current_cart_confirm"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            pos_service.clear(self.cart)
            self.refresh_cart()
            self.status_label.setText(translate("cart_cancelled"))
            self._focus_barcode_input()

    def suspend_cart(self):
        if not self._require_pos_operation(pos_operation_policy.OP_SUSPEND):
            return
        try:
            note, ok = QInputDialog.getText(self, translate("suspend_sale"), translate("suspended_sale_note"))
            if not ok:
                return
            pos_service.suspend(self.cart, note)
            self.cart = pos_service.new_cart(self._selected_warehouse_id() if hasattr(self, 'warehouse_combo') else None, self._selected_cashbox_id() if hasattr(self, 'cashbox_combo') else None)
            self.refresh_cart()
            show_toast(translate("sale_suspended"), "success", self)
        except POSException as e:
            show_toast(str(e), "warning", self)
        finally:
            self._focus_barcode_input()

    def resume_cart(self):
        if not self._require_pos_operation(pos_operation_policy.OP_RESUME):
            return
        if not pos_service.suspended_carts:
            show_toast(translate("no_suspended_sales"), "info", self)
            return
        labels = [f"{i+1}. {cart.note or cart.created_at} - {currency.format_amount(currency.convert(cart.total_usd, currency.storage_currency(), self.display_curr))}" for i, cart in enumerate(pos_service.suspended_carts)]
        choice, ok = QInputDialog.getItem(self, translate("resume_suspended_sale"), translate("choose_cart"), labels, 0, False)
        if not ok:
            return
        index = labels.index(choice)
        try:
            if self.cart.lines:
                pos_service.suspend(self.cart, translate("cart_before_resume"))
            self.cart = pos_service.resume(index)
            self.refresh_cart()
            show_toast(translate("sale_resumed"), "success", self)
        except POSException as e:
            show_toast(str(e), "error", self)
        finally:
            self._focus_barcode_input()

    def checkout(self):
        if not self._require_pos_operation(pos_operation_policy.OP_CHECKOUT):
            return
        try:
            self.refresh_shift_state()
            if self._pos_shifts_enabled() and not getattr(self, 'current_shift_id', None):
                raise POSException(translate('open_shift_before_checkout'))
            payment_method = self.payment_combo.currentData() or 'cash'
            paid_display = Decimal(str(self.paid_spin.value()))
            paid_usd = currency.convert(paid_display, self.display_curr, currency.storage_currency())
            if payment_method in ('cash', 'card') and paid_usd < self.cart.total_usd:
                reply = QMessageBox.question(self, translate("incomplete_payment"), translate("partial_payment_confirm"), QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            invoice_id = pos_service.checkout(self.cart, payment_method, paid_usd)
            show_toast(translate("sale_completed_invoice", invoice_id=invoice_id), "success", self)
            self._offer_print_receipt(invoice_id)
            self.cart = pos_service.new_cart(self._selected_warehouse_id() if hasattr(self, 'warehouse_combo') else None, self._selected_cashbox_id() if hasattr(self, 'cashbox_combo') else None)
            self.refresh_cart()
        except POSException as e:
            show_toast(str(e), "error", self)
        except Exception as e:
            show_toast(translate("checkout_failed", error=e), "error", self)
        finally:
            self._focus_barcode_input()

    def _offer_print_receipt(self, invoice_id):
        if not pos_operation_policy.can(pos_operation_policy.OP_PRINT_RECEIPT):
            return
        reply = QMessageBox.question(self, translate("print_receipt"), translate("print_thermal_receipt_confirm"), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            from core.services.invoice_service import invoice_service
            from printing.printing_service import printing_service
            inv = invoice_service.get(invoice_id)
            if inv:
                printing_service.invoice_print(inv, self, paper='thermal80')
        except Exception as e:
            show_toast(translate("receipt_print_failed", error=e), "warning", self)

    def showEvent(self, event):
        super().showEvent(event)
        self._focus_barcode_input()
