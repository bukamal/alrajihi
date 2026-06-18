# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox

from i18n import translate


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

    def workspace_save(self) -> None:
        raise NotImplementedError

    def workspace_print(self) -> None:
        QMessageBox.information(self, translate('printing'), translate('workspace.no_print_action'))

    def workspace_export(self) -> None:
        QMessageBox.information(self, translate('reports'), translate('workspace.no_export_action'))
