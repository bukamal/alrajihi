# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QMessageBox

from i18n import translate
from workspace.documents.document_contract import descriptor_for
from workspace.shell.workspace_tab_close import close_owning_workspace_tab
from core.services.sales_return_service import sales_return_service
from core.services.purchase_return_service import purchase_return_service
from views.widgets.returns_widget import (
    SalesReturnDialog,
    PurchaseReturnDialog,
    _ret_print_dialog,
)
from .components import (
    ReturnHeaderComponent,
    ReturnLinesComponent,
    ReturnSettlementComponent,
    ReturnActionsComponent,
)


class _ReturnDocumentMixin:
    LEGACY_TRANSACTION_ADAPTER = True
    DOCUMENT_DESCRIPTOR_BY_RETURN_KIND = {'sale': descriptor_for('sales_return'), 'purchase': descriptor_for('purchase_return')}
    """Legacy return document adapter for unit-aware return editors.

    TransactionDocumentTab is the official return shell. This adapter is retained only
    for emergency rollback when features/allow_legacy_transaction_documents is enabled.

    This is the Phase 49 boundary that replaces the Phase 47 generic bridge
    adapter for returns.  The Qt controls are still reused conservatively, but
    workspace commands, payload extraction, validation, printing and dirty state
    now pass through feature-level components instead of the generic dialog host.
    """

    dirtyChanged = pyqtSignal(bool)
    saved = pyqtSignal(object)
    titleChanged = pyqtSignal(str)

    return_kind = 'sale'
    service = sales_return_service

    def _init_document_tab(self, return_id=None) -> None:
        self.document_type = f'{self.return_kind}_return'
        self.document_id = return_id
        self.document_descriptor = self.DOCUMENT_DESCRIPTOR_BY_RETURN_KIND.get(self.return_kind)
        self.header_component = ReturnHeaderComponent(self)
        self.lines_component = ReturnLinesComponent(self, self.return_kind)
        self.settlement_component = ReturnSettlementComponent(self)
        self.actions_component = ReturnActionsComponent(self)
        self._embed_as_workspace_widget()
        self._install_document_dirty_tracking()
        self.setWindowTitle(self.workspace_title())

    def _embed_as_workspace_widget(self) -> None:
        try:
            self.setModal(False)
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
        except Exception:
            pass
        for name in ('title_bar', 'close_btn', 'min_btn', 'max_btn'):
            widget = getattr(self, name, None)
            if widget is not None:
                try:
                    widget.setVisible(False)
                except Exception:
                    pass

    def _install_document_dirty_tracking(self) -> None:
        widgets = [
            getattr(self, 'invoice_combo', None),
            getattr(self, 'date_edit', None),
            getattr(self, 'warehouse_combo', None),
            getattr(self, 'refund_spin', None),
            getattr(self, 'payment_method_combo', None),
            getattr(self, 'cashbox_combo', None),
            getattr(self, 'bank_combo', None),
            getattr(self, 'notes_edit', None),
        ]
        try:
            self.watch_dirty_widgets(widgets, reset=True)
        except Exception:
            pass
        try:
            self.lines_table.cellChanged.connect(lambda *_: self.mark_dirty())
        except Exception:
            pass
        self.reset_dirty()

    def mark_dirty(self):
        try:
            super().mark_dirty()
        except Exception:
            pass
        self.dirtyChanged.emit(True)

    def reset_dirty(self):
        try:
            super().reset_dirty()
        except Exception:
            pass
        self.dirtyChanged.emit(False)

    def is_dirty(self) -> bool:
        return bool(getattr(self, '_dirty', False))

    def can_close(self) -> bool:
        if hasattr(self, '_confirm_discard_changes'):
            return self._confirm_discard_changes()
        return True

    def workspace_title(self) -> str:
        base = translate('purchase_return') if self.return_kind == 'purchase' else translate('sales_return')
        if getattr(self, 'edit_return_id', None):
            return f"{base} #{self.edit_return_id}"
        return f"{base} *"

    def document_payload(self) -> dict:
        payload = {}
        payload.update(self.header_component.data())
        payload.update(self.settlement_component.data())
        payload['lines'] = self.lines_component.payload()
        return payload

    def request_workspace_close(self) -> bool:
        """Close the embedded return tab through the workspace lifecycle."""
        try:
            return bool(close_owning_workspace_tab(self))
        except Exception:
            QDialog.reject(self)
            return True

    def workspace_save(self) -> None:
        self._save_return_document(close_after_save=False)

    def workspace_print(self) -> None:
        _ret_print_dialog(self, self.return_kind, 'direct')

    def workspace_export(self) -> None:
        _ret_print_dialog(self, self.return_kind, 'direct')

    def _save_return_document(self, close_after_save: bool = False):
        ok, error_key = self.lines_component.validate()
        if not ok:
            QMessageBox.warning(self, translate('return_save_failed'), translate(error_key))
            return False
        try:
            payload = self.document_payload()
            if getattr(self, 'edit_return_id', None):
                self.service.update_return(self.edit_return_id, payload)
                saved_id = self.edit_return_id
            else:
                result = self.service.create_return(payload)
                saved_id = result.get('id') if isinstance(result, dict) else result
                if saved_id:
                    self.edit_return_id = saved_id
                    self.document_id = saved_id
            self.reset_dirty()
            self.saved.emit(saved_id or self.document_id)
            self.setWindowTitle(self.workspace_title().rstrip(' *'))
            self.titleChanged.emit(self.windowTitle())
            if close_after_save:
                self.request_workspace_close()
            return True
        except Exception as exc:
            QMessageBox.warning(self, translate('return_save_failed'), str(exc))
            return False

    def accept(self):
        self._save_return_document(close_after_save=True)


class SalesReturnEditorTab(_ReturnDocumentMixin, SalesReturnDialog):
    return_kind = 'sale'
    service = sales_return_service

    def __init__(self, parent=None, return_id=None, return_data=None) -> None:
        SalesReturnDialog.__init__(self, parent, return_id=return_id, return_data=return_data)
        self._init_document_tab(return_id=return_id)


class PurchaseReturnEditorTab(_ReturnDocumentMixin, PurchaseReturnDialog):
    return_kind = 'purchase'
    service = purchase_return_service

    def __init__(self, parent=None, return_id=None, return_data=None) -> None:
        PurchaseReturnDialog.__init__(self, parent, return_id=return_id, return_data=return_data)
        self._init_document_tab(return_id=return_id)
