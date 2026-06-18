# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Optional, Type

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QCheckBox, QTableWidget

from workspace.documents import BaseDocumentTab


class DialogDocumentTab(BaseDocumentTab):
    """Host legacy business dialogs as first-class workspace document tabs.

    This is a migration adapter, not a permanent dumping ground.  It lets large
    dialogs such as returns and vouchers run inside TabbedWorkspace while their
    internals are decomposed into smaller components in later phases.  The tab
    still exposes the common document commands consumed by UnifiedActionBar.
    """

    def __init__(
        self,
        document_type: str,
        dialog_cls: Type[QWidget],
        parent: Optional[QWidget] = None,
        document_id: Optional[int] = None,
        title: str = "",
        *dialog_args: Any,
        **dialog_kwargs: Any,
    ) -> None:
        super().__init__(document_type=document_type, document_id=document_id, parent=parent)
        self.dialog = dialog_cls(self, *dialog_args, **dialog_kwargs)
        self._embed_dialog_widget(self.dialog)
        self._connect_dialog_lifecycle()
        self._install_dirty_tracking()
        self.set_document_title(title or self.dialog.windowTitle() or document_type)
        self.set_dirty(False)

    def _embed_dialog_widget(self, dialog: QWidget) -> None:
        try:
            dialog.setModal(False)  # QDialog compatibility
        except Exception:
            pass
        try:
            dialog.setWindowFlags(Qt.Widget)
            dialog.setAttribute(Qt.WA_TranslucentBackground, False)
        except Exception:
            pass
        try:
            if hasattr(dialog, 'title_bar'):
                dialog.title_bar.setVisible(False)
            if hasattr(dialog, 'close_btn'):
                dialog.close_btn.setVisible(False)
            if hasattr(dialog, 'min_btn'):
                dialog.min_btn.setVisible(False)
            if hasattr(dialog, 'max_btn'):
                dialog.max_btn.setVisible(False)
        except Exception:
            pass
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(dialog)
        dialog.show()

    def _connect_dialog_lifecycle(self) -> None:
        if hasattr(self.dialog, 'accepted'):
            try:
                self.dialog.accepted.connect(self._on_dialog_saved)
            except Exception:
                pass
        if hasattr(self.dialog, 'saved'):
            try:
                self.dialog.saved.connect(self._on_dialog_saved)
            except Exception:
                pass
        if hasattr(self.dialog, 'dirtyChanged'):
            try:
                self.dialog.dirtyChanged.connect(self.set_dirty)
            except Exception:
                pass

    def _install_dirty_tracking(self) -> None:
        for child in self.dialog.findChildren((QLineEdit, QTextEdit, QPlainTextEdit)):
            try:
                child.textChanged.connect(lambda *_: self.set_dirty(True))
            except Exception:
                pass
        for child in self.dialog.findChildren(QComboBox):
            try:
                child.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
            except Exception:
                pass
        for child in self.dialog.findChildren((QSpinBox, QDoubleSpinBox)):
            try:
                child.valueChanged.connect(lambda *_: self.set_dirty(True))
            except Exception:
                pass
        for child in self.dialog.findChildren(QDateEdit):
            try:
                child.dateChanged.connect(lambda *_: self.set_dirty(True))
            except Exception:
                pass
        for child in self.dialog.findChildren(QCheckBox):
            try:
                child.stateChanged.connect(lambda *_: self.set_dirty(True))
            except Exception:
                pass
        for child in self.dialog.findChildren(QTableWidget):
            try:
                child.cellChanged.connect(lambda *_: self.set_dirty(True))
            except Exception:
                pass

    def _on_dialog_saved(self, *args: Any) -> None:
        self.set_dirty(False)
        document_id = args[0] if args else self.document_state.document_id
        self.saved.emit(document_id)
        new_title = self.dialog.windowTitle() or self.document_state.title
        self.set_document_title(new_title)

    def can_close(self) -> bool:
        if hasattr(self.dialog, '_confirm_discard_changes'):
            try:
                if not self.dialog._confirm_discard_changes():
                    return False
            except Exception:
                pass
        return super().can_close()

    def workspace_save(self) -> None:
        for name in ('workspace_save', 'save', 'on_save', 'accept'):
            method = getattr(self.dialog, name, None)
            if callable(method):
                method()
                return
        raise NotImplementedError(f'{self.document_state.document_type} does not expose a save action')

    def workspace_print(self) -> None:
        for name in ('workspace_print', 'print_invoice_professional', 'print_current', 'print_report'):
            method = getattr(self.dialog, name, None)
            if callable(method):
                method()
                return
        super().workspace_print()

    def workspace_export(self) -> None:
        for name in ('workspace_export', 'save_invoice_pdf', 'export_current', 'export'):
            method = getattr(self.dialog, name, None)
            if callable(method):
                method()
                return
        super().workspace_export()
