# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QMenu,
    QPushButton,
    QShortcut,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
)

from core.services.manufacturing_operation_policy import manufacturing_operation_policy
from core.services.manufacturing_service import manufacturing_service
from features.manufacturing.manufacturing_printing_bridge import manufacturing_printing_bridge
from core.services.product_service import product_service
from currency import currency
from features.dialog_documents import DialogDocumentTab
from features.manufacturing.components.production_lifecycle_summary_panel import ProductionLifecycleSummaryPanel
from features.manufacturing.grids.manufacturing_column_schema import (
    production_consumptions_schema,
    production_outputs_schema,
    production_reservations_schema,
)
from features.manufacturing.grids.production_lifecycle_grid import ProductionLifecycleGrid
from features.manufacturing.grids.production_lifecycle_model import ProductionLifecycleTableModel
from i18n import qt_layout_direction, translate
from utils import show_toast
from views.dialogs.production_details_dialog import ProductionDetailsDialog
from workspace.documents.base_document_tab import BaseDocumentTab


def _num(value, default=0):
    try:
        if value is None or value == '':
            return float(default)
        return float(Decimal(str(value)))
    except Exception:
        return float(default)


def _result_ok(result) -> tuple[bool, str]:
    if isinstance(result, tuple):
        ok = bool(result[0]) if result else False
        msg = str(result[1]) if len(result) > 1 else ''
        return ok, msg
    if result is False:
        return False, ''
    return True, ''


class LegacyProductionOrderDetailsTab(DialogDocumentTab):
    """Emergency fallback wrapper around the old ProductionDetailsDialog."""

    def __init__(self, parent=None, order_id: Optional[int] = None):
        super().__init__(
            document_type='production_order_details',
            dialog_cls=ProductionDetailsDialog,
            parent=parent,
            document_id=order_id,
            title=translate('production_details'),
            order_id=order_id,
        )

    def workspace_save(self) -> None:
        self.set_dirty(False)

    def workspace_print(self) -> None:
        method = getattr(self.dialog, 'print_order', None)
        if callable(method):
            method('preview')
            return
        super().workspace_print()

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('production_details')


class ProductionOrderDetailsTab(BaseDocumentTab):
    """Production-order lifecycle tab.

    Phase 190 replaces the embedded ProductionDetailsDialog with a service-backed
    tab showing reservations, consumptions and outputs in unified grids. Actions
    still go through ManufacturingService and ManufacturingOperationPolicy.
    """

    def __init__(self, parent=None, order_id: Optional[int] = None):
        super().__init__('production_order_details', document_id=order_id, parent=parent)
        self.order_id = order_id
        self.service = manufacturing_service
        self.order: dict = {}
        self.res_columns = production_reservations_schema()
        self.cons_columns = production_consumptions_schema()
        self.out_columns = production_outputs_schema()
        self.res_model = ProductionLifecycleTableModel(self.res_columns, 'reservations', self)
        self.cons_model = ProductionLifecycleTableModel(self.cons_columns, 'consumptions', self)
        self.out_model = ProductionLifecycleTableModel(self.out_columns, 'outputs', self)
        self._build_ui()
        self._install_shortcuts()
        self.refresh_all()
        self.set_dirty(False)

    def workspace_title(self) -> str:
        title = self.order.get('order_number') if isinstance(self.order, dict) else None
        return self.document_state.title or (f"{translate('production_details')} - {title}" if title else translate('production_details'))

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        self.header_card = QFrame(self)
        self.header_card.setObjectName('DocumentHeaderCard')
        header = QVBoxLayout(self.header_card)
        header.setContentsMargins(16, 14, 16, 14)
        top = QHBoxLayout()
        self.title_label = QLabel(translate('production_details'))
        self.title_label.setObjectName('DocumentTitle')
        top.addWidget(self.title_label)
        top.addStretch(1)
        self.refresh_btn = QPushButton(translate('refresh'))
        self.print_btn = QPushButton(translate('print'))
        self.pick_ticket_btn = QPushButton(translate('manufacturing_pick_ticket'))
        self.cost_report_btn = QPushButton(translate('manufacturing_cost_report'))
        self.close_btn = QPushButton(translate('close'))
        top.addWidget(self.refresh_btn)
        top.addWidget(self.print_btn)
        top.addWidget(self.pick_ticket_btn)
        top.addWidget(self.cost_report_btn)
        top.addWidget(self.close_btn)
        header.addLayout(top)

        self.info_label = QLabel('')
        self.info_label.setWordWrap(True)
        header.addWidget(self.info_label)

        actions = QHBoxLayout()
        self.start_btn = QPushButton(translate('start_production'))
        self.cancel_order_btn = QPushButton(translate('cancel_order'))
        self.consume_btn = QPushButton(translate('consume_materials'))
        self.complete_btn = QPushButton(translate('complete_production'))
        self.reverse_btn = QPushButton(translate('reverse_production'))
        self.reverse_btn.setObjectName('danger')
        for btn in (self.start_btn, self.cancel_order_btn, self.consume_btn, self.complete_btn, self.reverse_btn):
            actions.addWidget(btn)
        actions.addStretch(1)
        header.addLayout(actions)
        root.addWidget(self.header_card)

        self.tabs = QTabWidget(self)
        self.res_grid = ProductionLifecycleGrid(self.res_columns, self, identity='manufacturing.production.lifecycle.reservations')
        self.res_grid.setModel(self.res_model)
        self.res_grid.apply_named_preset('warehouse')
        self.cons_grid = ProductionLifecycleGrid(self.cons_columns, self, identity='manufacturing.production.lifecycle.consumptions')
        self.cons_grid.setModel(self.cons_model)
        self.cons_grid.apply_named_preset('accountant')
        self.cons_grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cons_grid.customContextMenuRequested.connect(self._show_consumption_menu)
        self.out_grid = ProductionLifecycleGrid(self.out_columns, self, identity='manufacturing.production.lifecycle.outputs')
        self.out_grid.setModel(self.out_model)
        self.out_grid.apply_named_preset('accountant')
        self.out_grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.out_grid.customContextMenuRequested.connect(self._show_output_menu)
        self.tabs.addTab(self.res_grid, translate('reservations_remaining'))
        self.tabs.addTab(self.cons_grid, translate('consumed_materials'))
        self.tabs.addTab(self.out_grid, translate('finished_product_group'))

        self.summary_panel = ProductionLifecycleSummaryPanel(self)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.summary_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self.refresh_btn.clicked.connect(self.refresh_all)
        self.print_btn.clicked.connect(self.workspace_print)
        self.pick_ticket_btn.clicked.connect(self.print_pick_ticket)
        self.cost_report_btn.clicked.connect(self.print_cost_report)
        self.close_btn.clicked.connect(self._close_parent_tab)
        self.start_btn.clicked.connect(self.start_production)
        self.cancel_order_btn.clicked.connect(self.cancel_production)
        self.consume_btn.clicked.connect(self.add_consumption)
        self.complete_btn.clicked.connect(self.complete_production)
        self.reverse_btn.clicked.connect(self.reverse_production)

        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#ProductionLifecycleSummaryPanel {
                border: 1px solid palette(mid); border-radius: 14px; background: palette(base);
            }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#PanelTitle { font-size: 14px; font-weight: 900; }
            QLabel#SummaryValue { font-weight: 800; }
            QPushButton#danger { font-weight: 900; }
            QTableView { gridline-color: palette(midlight); alternate-background-color: palette(alternate-base); }
        ''')

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Refresh, self, activated=self.refresh_all)
        QShortcut(QKeySequence.Print, self, activated=self.workspace_print)

    def refresh_all(self) -> None:
        if not self.order_id:
            return
        try:
            self.order = self.service.get_production_order(self.order_id) or {}
            if not self.order:
                show_toast(translate('production_order_not_found'), 'error', self)
                return
            self.res_model.load_rows(self.service.get_reservations(self.order_id))
            self.cons_model.load_rows(self.service.get_consumptions(self.order_id))
            self.out_model.load_rows(self.service.get_outputs(self.order_id))
            self._refresh_header()
            self._apply_operation_state()
            self.summary_panel.update_summary(
                reservations=self.res_model.summary(),
                consumptions=self.cons_model.summary(),
                outputs=self.out_model.summary(),
            )
            self.set_document_title(self.workspace_title())
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _refresh_header(self) -> None:
        order = self.order or {}
        status_map = {
            'planned': translate('status_planned'),
            'in_progress': translate('status_in_progress'),
            'completed': translate('status_completed'),
            'cancelled': translate('status_cancelled'),
        }
        title = order.get('order_number') or self.order_id or ''
        self.title_label.setText(f"{translate('production_details')} - {title}")
        self.info_label.setText(
            f"<b>{translate('product_label')}</b> {order.get('product_name', '')} &nbsp; "
            f"<b>{translate('planned_quantity_label')}</b> {order.get('planned_qty', 0)} &nbsp; "
            f"<b>{translate('produced_quantity_label')}</b> {order.get('produced_qty', 0)} &nbsp; "
            f"<b>{translate('status_label')}</b> {status_map.get(order.get('status', 'planned'), translate('status_planned'))}<br>"
            f"<b>{translate('raw_warehouse_long_label')}</b> {order.get('raw_warehouse_name') or '-'} &nbsp; "
            f"<b>{translate('output_warehouse_long_label')}</b> {order.get('output_warehouse_name') or '-'} &nbsp; "
            f"<b>{translate('start_date_label')}</b> {order.get('start_date', '-')}"
        )

    def _apply_operation_state(self) -> None:
        status = (self.order or {}).get('status', 'planned')
        can_start = status == 'planned' and self.service.can_operation(manufacturing_operation_policy.OP_ORDER_START)
        can_cancel = status == 'planned' and self.service.can_operation(manufacturing_operation_policy.OP_ORDER_CANCEL)
        can_consume = status == 'in_progress' and self.service.can_operation(manufacturing_operation_policy.OP_MATERIAL_CONSUME)
        can_complete = status == 'in_progress' and self.service.can_operation(manufacturing_operation_policy.OP_OUTPUT_COMPLETE)
        can_reverse = status in ('in_progress', 'completed') and self.service.can_operation(manufacturing_operation_policy.OP_ORDER_REVERSE)
        can_print = self.service.can_operation(manufacturing_operation_policy.OP_PRINT)
        self.start_btn.setVisible(can_start)
        self.cancel_order_btn.setVisible(can_cancel)
        self.consume_btn.setVisible(can_consume)
        self.complete_btn.setVisible(can_complete)
        self.reverse_btn.setVisible(can_reverse)
        self.print_btn.setEnabled(can_print)
        self.pick_ticket_btn.setEnabled(can_print)
        self.cost_report_btn.setEnabled(can_print)

    def _print_payload(self) -> dict:
        return {
            'order': self.service.get_production_order(self.order_id) or {},
            'reservations': self.service.get_reservations(self.order_id) or [],
            'consumptions': self.service.get_consumptions(self.order_id) or [],
            'outputs': self.service.get_outputs(self.order_id) or [],
        }

    def workspace_print(self) -> None:
        try:
            manufacturing_printing_bridge.production_order_print(int(self.order_id), self)
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def print_pick_ticket(self) -> None:
        try:
            manufacturing_printing_bridge.pick_ticket_print(int(self.order_id), self)
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def print_cost_report(self) -> None:
        try:
            manufacturing_printing_bridge.cost_report_print(int(self.order_id), self)
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def start_production(self) -> None:
        ok, msg = _result_ok(self.service.start_production(self.order_id))
        if ok:
            show_toast(translate('production_started'), 'success', self)
            self.saved.emit(self.order_id)
            self.refresh_all()
        else:
            QMessageBox.critical(self, translate('error'), msg)

    def cancel_production(self) -> None:
        reply = QMessageBox.question(self, translate('confirm_delete'), translate('confirm_cancel_production'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        ok, msg = _result_ok(self.service.cancel_production(self.order_id))
        if ok:
            show_toast(translate('production_cancelled'), 'success', self)
            self.saved.emit(self.order_id)
            self.refresh_all()
        else:
            QMessageBox.critical(self, translate('error'), msg)

    def add_consumption(self) -> None:
        remaining_rows = [row for row in self.res_model.lines if _num(row.get('remaining_qty')) > 0]
        if not remaining_rows:
            show_toast(translate('all_materials_consumed'), 'info', self)
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(translate('consume_materials'))
        dlg.setLayoutDirection(qt_layout_direction())
        layout = QFormLayout(dlg)
        item_combo = QComboBox(dlg)
        for row in remaining_rows:
            item_combo.addItem(
                row.get('item', '') + translate('material_remaining_suffix', remaining=_num(row.get('remaining_qty'))),
                row,
            )
        layout.addRow(translate('material_label'), item_combo)
        qty_spin = QDoubleSpinBox(dlg)
        qty_spin.setRange(0.0001, 999999999)
        qty_spin.setDecimals(4)
        layout.addRow(translate('consumed_quantity_label'), qty_spin)
        cost_spin = QDoubleSpinBox(dlg)
        cost_spin.setRange(0, 999999999)
        cost_spin.setDecimals(4)
        try:
            cost_spin.setPrefix(f"{currency.get_currency_symbol()} ")
        except Exception:
            pass
        layout.addRow(translate('unit_price_label'), cost_spin)
        buttons = QHBoxLayout()
        save_btn = QPushButton(translate('register'), dlg)
        cancel_btn = QPushButton(translate('cancel'), dlg)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        def update_inputs():
            row = item_combo.currentData() or {}
            max_qty = max(_num(row.get('remaining_qty')), 0.0001)
            qty_spin.setMaximum(max_qty)
            qty_spin.setValue(min(max_qty, max(qty_spin.value(), 1.0)))
            try:
                item_id = row.get('item_id')
                it = product_service.item_by_id(item_id) if item_id else None
                if it:
                    price = _num(it.get('average_cost'), 0) or _num(it.get('purchase_price'), 0)
                    price_display = currency.to_display(price)
                    cost_spin.setValue(_num(price_display, 0))
            except Exception:
                pass

        def consume():
            row = item_combo.currentData() or {}
            item_id = row.get('item_id')
            if not item_id:
                return
            cost_usd = currency.from_display(cost_spin.value())
            ok, msg = _result_ok(self.service.consume_material(self.order_id, item_id, qty_spin.value(), cost_usd))
            if ok:
                show_toast(translate('consumption_registered'), 'success', self)
                dlg.accept()
                self.saved.emit(self.order_id)
                self.refresh_all()
            else:
                QMessageBox.critical(dlg, translate('error'), msg)

        item_combo.currentIndexChanged.connect(update_inputs)
        save_btn.clicked.connect(consume)
        cancel_btn.clicked.connect(dlg.reject)
        update_inputs()
        dlg.exec()

    def complete_production(self) -> None:
        remaining = [row for row in self.res_model.lines if _num(row.get('remaining_qty')) > 0.001]
        if remaining:
            row = remaining[0]
            QMessageBox.warning(self, translate('missing_consumption_title'), translate('missing_consumption_msg', item=row.get('item') or '-', remaining=_num(row.get('remaining_qty'))))
            return
        planned = _num((self.order or {}).get('planned_qty'))
        produced = _num((self.order or {}).get('produced_qty'))
        max_qty = planned - produced
        if max_qty <= 0:
            QMessageBox.warning(self, translate('warning'), translate('planned_quantity_completed'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(translate('complete_production'))
        dlg.setLayoutDirection(qt_layout_direction())
        layout = QFormLayout(dlg)
        qty_spin = QDoubleSpinBox(dlg)
        qty_spin.setRange(0.0001, max_qty)
        qty_spin.setDecimals(4)
        qty_spin.setValue(max_qty)
        layout.addRow(translate('actual_produced_quantity'), qty_spin)
        buttons = QHBoxLayout()
        save_btn = QPushButton(translate('complete'), dlg)
        cancel_btn = QPushButton(translate('cancel'), dlg)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        def complete():
            ok, msg = _result_ok(self.service.complete_production(self.order_id, qty_spin.value()))
            if ok:
                show_toast(translate('production_completed'), 'success', self)
                dlg.accept()
                self.saved.emit(self.order_id)
                self.refresh_all()
            else:
                QMessageBox.critical(dlg, translate('error'), msg)

        save_btn.clicked.connect(complete)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()

    def reverse_production(self) -> None:
        reply = QMessageBox.question(self, translate('confirm_reverse_title'), translate('confirm_reverse_production'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        ok, msg = _result_ok(self.service.reverse_production_order(self.order_id))
        if ok:
            show_toast(msg or translate('production_cancelled'), 'success', self)
            self.saved.emit(self.order_id)
            self.refresh_all()
        else:
            QMessageBox.critical(self, translate('error'), msg)

    def _show_consumption_menu(self, pos) -> None:
        index = self.cons_grid.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        cons_id = self.cons_model.get_id(row)
        if not cons_id or not self.service.can_operation(manufacturing_operation_policy.OP_CONSUMPTION_DELETE):
            return
        menu = QMenu(self)
        menu.addAction(translate('delete_consumption'), lambda: self.delete_consumption(cons_id))
        menu.exec(self.cons_grid.viewport().mapToGlobal(pos))

    def _show_output_menu(self, pos) -> None:
        index = self.out_grid.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        out_id = self.out_model.get_id(row)
        if not out_id or not self.service.can_operation(manufacturing_operation_policy.OP_OUTPUT_DELETE):
            return
        menu = QMenu(self)
        menu.addAction(translate('delete_output'), lambda: self.delete_output(out_id))
        menu.exec(self.out_grid.viewport().mapToGlobal(pos))

    def delete_consumption(self, cons_id) -> None:
        reply = QMessageBox.question(self, translate('confirm_delete'), translate('confirm_delete_consumption'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        ok, msg = _result_ok(self.service.delete_consumption(cons_id))
        if ok:
            show_toast(translate('consumption_deleted'), 'success', self)
            self.saved.emit(self.order_id)
            self.refresh_all()
        else:
            QMessageBox.critical(self, translate('error'), msg)

    def delete_output(self, out_id) -> None:
        reply = QMessageBox.question(self, translate('confirm_delete'), translate('confirm_delete_output'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        ok, msg = _result_ok(self.service.delete_output(out_id))
        if ok:
            show_toast(translate('output_deleted'), 'success', self)
            self.saved.emit(self.order_id)
            self.refresh_all()
        else:
            QMessageBox.critical(self, translate('error'), msg)

    def _close_parent_tab(self) -> None:
        # Phase351: production lifecycle close uses the shared workspace lifecycle.
        self.request_workspace_close()
