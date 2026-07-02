# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget

from core.services.catalog_service import catalog_service
from core.services.invoice_service import invoice_service
from currency import currency
from i18n import qt_layout_direction, translate as tr
from offline_read import is_offline_read_error, notify_offline_read
from ui.inline_quick_create import InlineQuickCreatePanel, quick_create_can


def _field_label(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text if str(text).endswith(':') else f"{text}:", parent)
    label.setObjectName('FieldLabel')
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return label


class VoucherLinkPanel(QWidget):
    """Party and invoice linkage for receipt/payment vouchers.

    Phase461 extends the Phase460 inline quick-create system into vouchers.
    Customers and suppliers can be created and selected from the same voucher
    surface without dialogs or new workspace tabs.
    """

    changed = pyqtSignal()
    remainingSelected = pyqtSignal(object)

    def __init__(self, parent=None, voucher=None) -> None:
        super().__init__(parent)
        self.setObjectName('VoucherLinkPanel')
        self.setProperty('phase461InlineQuickCreateHost', True)
        self.setLayoutDirection(qt_layout_direction())
        self.voucher = voucher or {}
        self._invoice_remaining_by_id: dict[int, Decimal] = {}
        self._loading = False
        self._field_labels: dict[str, QLabel] = {}

        layout = QGridLayout(self)
        self._layout = layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 1)

        self.customer_combo = QComboBox()
        self.customer_combo.setObjectName('voucher_customer_combo')
        self.customer_combo.addItem(tr('no_customer'), None)
        self._reload_customer_options()

        self.supplier_combo = QComboBox()
        self.supplier_combo.setObjectName('voucher_supplier_combo')
        self.supplier_combo.addItem(tr('no_supplier'), None)
        self._reload_supplier_options()

        self.invoice_combo = QComboBox()
        self.invoice_combo.setObjectName('voucher_invoice_combo')
        self.invoice_combo.addItem(tr('no_invoice'), None)

        for widget in (self.customer_combo, self.supplier_combo, self.invoice_combo):
            widget.setMinimumHeight(30)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.quick_customer_btn = self._quick_button('customer', tr('inline_quick_create_customer_tooltip'))
        self.quick_supplier_btn = self._quick_button('supplier', tr('inline_quick_create_supplier_tooltip'))
        self.quick_customer_btn.clicked.connect(self.quick_customer_panel.toggle_panel)
        self.quick_supplier_btn.clicked.connect(self.quick_supplier_panel.toggle_panel)

        self.customer_field = self._combo_with_inline_button('VoucherCustomerInlineCreateField', self.customer_combo, self.quick_customer_btn)
        self.supplier_field = self._combo_with_inline_button('VoucherSupplierInlineCreateField', self.supplier_combo, self.quick_supplier_btn)

        self._add_pair(layout, 'customer', 0, 0, tr('customer_label'), self.customer_field)
        self._add_pair(layout, 'supplier', 0, 0, tr('supplier_label'), self.supplier_field)
        self._add_pair(layout, 'invoice', 0, 2, tr('invoice_label'), self.invoice_combo)

        self.quick_customer_panel = InlineQuickCreatePanel('customer', self)
        self.quick_customer_panel.setObjectName('VoucherInlineQuickCustomerPanel')
        self.quick_customer_panel.created.connect(self._on_inline_party_created)
        self.quick_customer_panel.setVisible(False)
        # Phase467: customer quick-create floats above the voucher form.

        self.quick_supplier_panel = InlineQuickCreatePanel('supplier', self)
        self.quick_supplier_panel.setObjectName('VoucherInlineQuickSupplierPanel')
        self.quick_supplier_panel.created.connect(self._on_inline_party_created)
        self.quick_supplier_panel.setVisible(False)
        # Phase467: supplier quick-create floats above the voucher form.

        self.customer_combo.currentIndexChanged.connect(lambda *_: (self.update_invoice_list(), self.changed.emit()))
        self.supplier_combo.currentIndexChanged.connect(lambda *_: (self.update_invoice_list(), self.changed.emit()))
        self.invoice_combo.currentIndexChanged.connect(lambda *_: (self._emit_remaining(), self.changed.emit()))

        self._refresh_inline_create_state()
        if isinstance(voucher, dict):
            self.load(voucher)

    def _quick_button(self, entity: str, tooltip: str) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName(f'VoucherInlineQuick{entity.title().replace("_", "")}Button')
        button.setProperty('visualRole', 'document_inline_create_action')
        button.setProperty('quickCreateEntity', entity)
        button.setText('+')
        button.setToolTip(tooltip)
        return button

    def _combo_with_inline_button(self, object_name: str, combo: QComboBox, button: QToolButton) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName(object_name)
        frame.setProperty('voucherInlineQuickCreateField', True)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(combo, 1)
        layout.addWidget(button)
        return frame

    def _add_pair(self, layout: QGridLayout, key: str, row: int, col: int, label_text: str, widget: QWidget) -> None:
        label = _field_label(label_text, self)
        self._field_labels[key] = label
        layout.addWidget(label, row, col)
        layout.addWidget(widget, row, col + 1)

    def _set_field_visible(self, key: str, widget: QWidget, visible: bool) -> None:
        label = self._field_labels.get(key)
        if label is not None:
            label.setVisible(visible)
        widget.setVisible(visible)

    def _refresh_inline_create_state(self) -> None:
        for entity, button in (('customer', self.quick_customer_btn), ('supplier', self.quick_supplier_btn)):
            allowed = quick_create_can(entity)
            button.setEnabled(allowed)
            button.setToolTip(tr(f'inline_quick_create_{entity}_tooltip') if allowed else tr('inline_quick_create_permission_denied'))

    def _reload_customer_options(self, select_id=None) -> None:
        current = select_id if select_id is not None else self.customer_combo.currentData() if hasattr(self, 'customer_combo') else None
        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        self.customer_combo.addItem(tr('no_customer'), None)
        for customer in self._safe_customers():
            self.customer_combo.addItem(customer.get('name', ''), customer.get('id'))
        if current is not None:
            idx = self.customer_combo.findData(current)
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)
        self.customer_combo.blockSignals(False)

    def _reload_supplier_options(self, select_id=None) -> None:
        current = select_id if select_id is not None else self.supplier_combo.currentData() if hasattr(self, 'supplier_combo') else None
        self.supplier_combo.blockSignals(True)
        self.supplier_combo.clear()
        self.supplier_combo.addItem(tr('no_supplier'), None)
        for supplier in self._safe_suppliers():
            self.supplier_combo.addItem(supplier.get('name', ''), supplier.get('id'))
        if current is not None:
            idx = self.supplier_combo.findData(current)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        self.supplier_combo.blockSignals(False)

    def _safe_customers(self):
        try:
            return catalog_service.customers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('customer_voucher_list'))
                return []
            raise

    def _safe_suppliers(self):
        try:
            return catalog_service.suppliers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('supplier_voucher_list'))
                return []
            raise

    def _on_inline_party_created(self, entity_type: str, result: dict) -> None:
        target_id = result.get('id')
        if entity_type == 'customer':
            self._reload_customer_options(target_id)
            self.customer_combo.setCurrentIndex(max(0, self.customer_combo.findData(target_id)))
        elif entity_type == 'supplier':
            self._reload_supplier_options(target_id)
            self.supplier_combo.setCurrentIndex(max(0, self.supplier_combo.findData(target_id)))
        else:
            return
        self.update_invoice_list()
        self.changed.emit()

    def load(self, voucher: dict) -> None:
        self._loading = True
        if voucher.get('customer_id'):
            idx = self.customer_combo.findData(voucher.get('customer_id'))
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)
        if voucher.get('supplier_id'):
            idx = self.supplier_combo.findData(voucher.get('supplier_id'))
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        self._loading = False

    def set_voucher_type(self, voucher_type: str) -> None:
        is_receipt = voucher_type == 'receipt'
        is_payment = voucher_type == 'payment'
        self._set_field_visible('customer', self.customer_field, is_receipt)
        self._set_field_visible('supplier', self.supplier_field, is_payment)
        self._set_field_visible('invoice', self.invoice_combo, is_receipt or is_payment)
        if not is_receipt:
            self.quick_customer_panel.setVisible(False)
        if not is_payment:
            self.quick_supplier_panel.setVisible(False)
        self.update_invoice_list(voucher_type)

    def _voucher_old_amount_for_invoice(self, invoice_id) -> Decimal:
        if not self.voucher or self.voucher.get('invoice_id') != invoice_id:
            return Decimal('0')
        try:
            return Decimal(str(self.voucher.get('amount') or 0))
        except Exception:
            return Decimal('0')

    def _add_invoice_option(self, inv: dict) -> None:
        try:
            inv_id = inv.get('id')
            remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0))) + self._voucher_old_amount_for_invoice(inv_id)
        except Exception:
            remaining = Decimal('0')
        if remaining <= 0:
            return
        self._invoice_remaining_by_id[inv_id] = remaining
        amount_label = currency.format_base_amount(remaining)
        self.invoice_combo.addItem(tr('remaining_invoice_amount', reference=inv.get('reference', inv_id), amount=amount_label), inv_id)

    def update_invoice_list(self, voucher_type: str | None = None) -> None:
        voucher_type = voucher_type or self._infer_type()
        entity_id = self.customer_combo.currentData() if voucher_type == 'receipt' else self.supplier_combo.currentData() if voucher_type == 'payment' else None
        self.invoice_combo.blockSignals(True)
        self.invoice_combo.clear()
        self._invoice_remaining_by_id = {}
        self.invoice_combo.addItem(tr('no_invoice'), None)
        if entity_id:
            invoices = invoice_service.unpaid_invoices(
                inv_type='sale' if voucher_type == 'receipt' else 'purchase',
                customer_id=entity_id if voucher_type == 'receipt' else None,
                supplier_id=entity_id if voucher_type == 'payment' else None,
                limit=100,
            )
            seen = set()
            for inv in invoices:
                seen.add(inv.get('id'))
                self._add_invoice_option(inv)
            current_invoice_id = self.voucher.get('invoice_id') if self.voucher else None
            if current_invoice_id and current_invoice_id not in seen:
                current = invoice_service.get(current_invoice_id)
                if current:
                    self._add_invoice_option(current)
        self.invoice_combo.blockSignals(False)
        if self.voucher.get('invoice_id'):
            idx = self.invoice_combo.findData(self.voucher.get('invoice_id'))
            if idx >= 0:
                self.invoice_combo.setCurrentIndex(idx)
        self._emit_remaining()

    def _infer_type(self) -> str:
        if self.customer_combo.currentData():
            return 'receipt'
        if self.supplier_combo.currentData():
            return 'payment'
        return 'expense'

    def _emit_remaining(self) -> None:
        if self._loading:
            return
        invoice_id = self.invoice_combo.currentData()
        remaining = self._invoice_remaining_by_id.get(invoice_id)
        if remaining and remaining > 0:
            self.remainingSelected.emit(remaining)

    def payload(self, voucher_type: str) -> dict:
        return {
            'customer_id': self.customer_combo.currentData() if voucher_type == 'receipt' else None,
            'supplier_id': self.supplier_combo.currentData() if voucher_type == 'payment' else None,
            'invoice_id': self.invoice_combo.currentData() or None,
        }
