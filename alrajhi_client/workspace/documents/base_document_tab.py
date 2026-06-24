# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox

from i18n import translate
from .document_contract import descriptor_for
from .document_permission_binder import DocumentPermissionBinder
from .document_layout_policy import apply_document_layout_policy


@dataclass
class DocumentState:
    """Runtime state for a business document opened inside the workspace."""

    document_type: str
    document_id: Optional[int] = None
    title: str = ""
    dirty: bool = False


class BaseDocumentTab(QWidget):
    """Base class for ERP document tabs.

    It provides the command surface consumed by UnifiedActionBar/MainWindow:
    workspace_save(), workspace_print(), workspace_export(), can_close(), and
    a dirtyChanged signal used by TabbedWorkspace.  Concrete feature tabs keep
    persistence behind services/gateways.
    """

    dirtyChanged = pyqtSignal(bool)
    saved = pyqtSignal(object)
    titleChanged = pyqtSignal(str)

    def __init__(self, document_type: str, document_id: Optional[int] = None, parent=None) -> None:
        super().__init__(parent)
        self.document_state = DocumentState(document_type=document_type, document_id=document_id)
        self.document_descriptor = descriptor_for(document_type)
        self.document_permission_binder = DocumentPermissionBinder(self.document_descriptor)
        self._document_permissions_applied = False


    def document_id_for_permissions(self):
        return self.document_state.document_id

    def can_document_action(self, action: str) -> bool:
        return self.document_permission_binder.can(action, document_id=self.document_id_for_permissions())

    def document_permission_matrix(self) -> dict:
        return self.document_permission_binder.matrix(document_id=self.document_id_for_permissions())

    def apply_document_permissions(self) -> dict:
        return self.document_permission_binder.apply_to_widget_buttons(self, document_id=self.document_id_for_permissions())

    def permission_denied_message(self, action: str) -> str:
        try:
            from core.services.permission_service import permission_service
            key = self.document_permission_binder.permission_key_for(action, document_id=self.document_id_for_permissions())
            return permission_service.denied_message(key)
        except Exception:
            return translate('workspace.permission_denied')

    def showEvent(self, event):
        super().showEvent(event)
        try:
            self.apply_document_permissions()
        except Exception:
            pass
        try:
            self.apply_document_layout_profile()
        except Exception:
            pass

    def apply_document_layout_profile(self, *, kind: Optional[str] = None, inline: Optional[bool] = None) -> str:
        """Apply the canonical visual document layout policy.

        Phase381: all document editors declare one of three structural families
        (card form, financial document, or tabular document). Inline hosts call
        this with ``inline=True``; standalone tabs call it automatically on
        showEvent.
        """
        return apply_document_layout_policy(self, kind=kind, inline=inline)

    def set_document_title(self, title: str) -> None:
        self.document_state.title = title
        self.setWindowTitle(title)
        self.titleChanged.emit(title)

    def set_dirty(self, dirty: bool = True) -> None:
        dirty = bool(dirty)
        if self.document_state.dirty == dirty:
            return
        self.document_state.dirty = dirty
        self.dirtyChanged.emit(dirty)

    def is_dirty(self) -> bool:
        return bool(self.document_state.dirty)

    def can_close(self) -> bool:
        if not self.is_dirty():
            return True
        reply = QMessageBox.question(
            self,
            translate('workspace.unsaved_title'),
            translate('workspace.unsaved_close'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes


    def request_workspace_close(self) -> bool:
        """Close this document through the owning workspace tab lifecycle.

        Phase350: embedded document close buttons must behave exactly like the
        tab-bar X button, including unsaved-change confirmation, safe neighbour
        selection, and fixed Dashboard fallback.
        """
        try:
            from workspace.shell.functional_close_policy import request_function_workspace_close
            function_key = getattr(self.document_descriptor, 'module_key', None) or getattr(self.document_state, 'document_type', None)
            return bool(request_function_workspace_close(self, function_key=function_key))
        except Exception:
            try:
                from workspace.shell.workspace_tab_close import close_owning_workspace_tab
                return bool(close_owning_workspace_tab(self))
            except Exception:
                try:
                    self.close()
                    return True
                except Exception:
                    return False

    def close_workspace_tab(self) -> bool:
        """Compatibility alias for document widgets and action bars."""
        return self.request_workspace_close()

    def workspace_save(self) -> None:
        raise NotImplementedError

    def workspace_print(self) -> None:
        if not self.can_document_action('print'):
            QMessageBox.warning(self, translate('printing'), self.permission_denied_message('print'))
            return
        QMessageBox.information(self, translate('printing'), translate('workspace.no_print_action'))

    def workspace_export(self) -> None:
        if not self.can_document_action('export'):
            QMessageBox.warning(self, translate('reports'), self.permission_denied_message('export'))
            return
        QMessageBox.information(self, translate('reports'), translate('workspace.no_export_action'))
