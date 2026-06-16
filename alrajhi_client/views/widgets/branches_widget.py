# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QCheckBox, QDialog, QFormLayout, QMessageBox, QDialogButtonBox, QTextEdit,
    QHeaderView, QTableView
)
from PyQt5.QtCore import Qt

from core.services.branch_service import branch_service
from models.table_models import GenericTableModel
from views.custom_table_view import CustomTableView
from utils import show_toast
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog
from i18n import translate, qt_layout_direction


class BranchDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data or {}
        self.setWindowTitle(translate('new_branch') if not data else translate('edit_branch'))
        self.setLayoutDirection(qt_layout_direction())
        self.resize(460, 360)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(self.data.get('name', ''))
        self.code_edit = QLineEdit(self.data.get('code', ''))
        self.address_edit = QLineEdit(self.data.get('address', ''))
        self.phone_edit = QLineEdit(self.data.get('phone', ''))
        self.notes_edit = QTextEdit(self.data.get('notes', ''))
        self.notes_edit.setMaximumHeight(90)
        self.active_check = QCheckBox(translate('active'))
        self.active_check.setChecked(bool(int(self.data.get('is_active', 1) or 0)))
        form.addRow(translate('branch_name_label'), self.name_edit)
        form.addRow(translate('code_label'), self.code_edit)
        form.addRow(translate('address_label'), self.address_edit)
        form.addRow(translate('phone_label'), self.phone_edit)
        form.addRow(translate('notes_label'), self.notes_edit)
        form.addRow('', self.active_check)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(translate('save'))
        buttons.button(QDialogButtonBox.Cancel).setText(translate('cancel'))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        apply_modern_dialog(self, translate('new_branch') if not data else translate('edit_branch'))
        self.name_edit.setFocus()

    def payload(self):
        return {
            'name': self.name_edit.text().strip(),
            'code': self.code_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'is_active': 1 if self.active_check.isChecked() else 0,
        }


class BranchesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._setup_ui()
        apply_modern_widget(self, translate('branches_title_icon'), translate('branches_subtitle'))
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel(translate('branches_manage_title'))
        title.setObjectName('sectionTitle')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translate('branches_search_placeholder'))
        self.search_edit.textChanged.connect(self.refresh)
        self.show_archived = QCheckBox(translate('show_archived'))
        self.show_archived.toggled.connect(self.refresh)
        add_btn = QPushButton(translate('new_branch_btn'))
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_branch)
        edit_btn = QPushButton(translate('edit_btn'))
        edit_btn.clicked.connect(self.edit_branch)
        archive_btn = QPushButton(translate('archive_btn'))
        archive_btn.clicked.connect(self.archive_branch)
        default_btn = QPushButton('⭐ تعيين كفرع افتراضي')
        default_btn.clicked.connect(self.set_default_branch)
        refresh_btn = QPushButton(translate('refresh'))
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addWidget(self.search_edit, 1)
        header.addWidget(self.show_archived)
        header.addWidget(add_btn)
        header.addWidget(edit_btn)
        header.addWidget(archive_btn)
        header.addWidget(default_btn)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        self.table = CustomTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.doubleClicked.connect(lambda _idx: self.edit_branch())
        layout.addWidget(self.table)
        self.status = QLabel()
        self.status.setObjectName('mutedLabel')
        layout.addWidget(self.status)

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(self, 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        elif hasattr(self, 'refresh'):
            self.refresh()


    def refresh(self):
        branch_service.bootstrap()
        text = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ''
        include_archived = self.show_archived.isChecked() if hasattr(self, 'show_archived') else False
        rows = []
        for branch in branch_service.branches(include_archived=include_archived):
            if text and text not in str(branch.get('name', '')).lower() and text not in str(branch.get('code', '')).lower():
                continue
            archived = bool(branch.get('deleted_at')) or int(branch.get('is_active') or 0) == 0
            rows.append({
                'id': branch.get('id'),
                'name': branch.get('name', ''),
                'code': branch.get('code') or '—',
                'address': branch.get('address') or '—',
                'phone': branch.get('phone') or '—',
                'warehouse_count': int(branch.get('warehouse_count') or 0),
                'is_default': translate('yes') if int(branch.get('is_default') or 0) == 1 else translate('no'),
                'status': translate('archived') if archived else translate('active'),
                'notes': branch.get('notes') or '',
            })
        headers = [translate('branch'), translate('code'), translate('address'), translate('phone'), translate('warehouse_count'), translate('is_default'), translate('status'), translate('notes')]
        keys = ['name', 'code', 'address', 'phone', 'warehouse_count', 'is_default', 'status', 'notes']
        self.model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.status.setText(translate('branches_count', count=len(rows)))

    def _selected_id(self):
        if not hasattr(self, 'model'):
            return None
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        row = rows[0].row()
        try:
            return self.model.get_row(row).get('id')
        except Exception:
            return None

    def add_branch(self):
        dlg = BranchDialog(self)
        if dlg.exec_():
            try:
                branch_service.add_branch(dlg.payload())
                show_toast(self, translate('branch_created'), 'success')
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, translate('error'), str(e))

    def edit_branch(self):
        branch_id = self._selected_id()
        if not branch_id:
            QMessageBox.information(self, translate('edit'), translate('select_branch_first'))
            return
        data = branch_service.branch_by_id(branch_id)
        if not data:
            QMessageBox.warning(self, translate('error'), translate('branch_not_found'))
            return
        dlg = BranchDialog(self, data)
        if dlg.exec_():
            try:
                branch_service.update_branch(branch_id, dlg.payload())
                show_toast(self, translate('branch_updated'), 'success')
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, translate('error'), str(e))


    def set_default_branch(self):
        branch_id = self._selected_id()
        if not branch_id:
            QMessageBox.information(self, translate('branches_title'), translate('select_branch_first'))
            return
        try:
            branch_service.set_default_branch(branch_id)
            show_toast(self, 'تم تعيين الفرع الافتراضي', 'success')
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, translate('error'), str(e))

    def archive_branch(self):
        branch_id = self._selected_id()
        if not branch_id:
            QMessageBox.information(self, translate('archive'), translate('select_branch_first'))
            return
        if QMessageBox.question(self, translate('confirm'), translate('archive_branch_confirm')) != QMessageBox.Yes:
            return
        try:
            branch_service.archive_branch(branch_id)
            show_toast(self, translate('branch_archived'), 'success')
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, translate('error'), str(e))
