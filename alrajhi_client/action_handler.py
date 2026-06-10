# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMenu, QAction, QMessageBox, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
import qtawesome as qta
from utils import show_toast

class BaseActionHandler:
    """
    كلاس مختلط (mixin) يضيف إجراءات موحدة لأي واجهة تحتوي على جدول.
    يجب أن تحتوي الواجهة على الخصائص التالية:
        - self.table (QTableView أو مشتق)
        - self.model (نموذج الجدول)
        - self.add_item()   (دالة للإضافة)
        - self.edit_item()  (دالة للتعديل، تستقبل index)
        - self.delete_item() (دالة للحذف، تستقبل id)
        - self.refresh()    (دالة لتحديث البيانات)
        - self.export_to_excel() (دالة لتصدير Excel)
        - self.print_table() (دالة لطباعة الجدول)
    """
    def setup_base_actions(self):
        """يجب استدعاؤها في __init__ بعد إنشاء الجدول"""
        self._setup_shortcuts()
        self._setup_context_menu()
        self._connect_table_signals()

    def _setup_shortcuts(self):
        """تثبيت الاختصارات العامة"""
        self.add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.add_shortcut.activated.connect(self._on_add_shortcut)
        self.edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.edit_shortcut.activated.connect(self._on_edit_shortcut)
        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.delete_shortcut.activated.connect(self._on_delete_shortcut)
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self._on_refresh_shortcut)
        self.print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.print_shortcut.activated.connect(self._on_print_shortcut)
        self.export_shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        self.export_shortcut.activated.connect(self._on_export_shortcut)

    def _setup_context_menu(self):
        if hasattr(self, 'table'):
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _connect_table_signals(self):
        if hasattr(self, 'table') and hasattr(self, 'edit_item'):
            self.table.doubleClicked.connect(self._on_double_click)

    def _on_add_shortcut(self):
        if hasattr(self, 'add_item'):
            self.add_item()

    def _on_edit_shortcut(self):
        if hasattr(self, 'edit_item'):
            idx = self.table.currentIndex()
            if idx.isValid():
                self.edit_item(idx)
            else:
                show_toast("الرجاء تحديد صف أولاً", "warning", self)

    def _on_delete_shortcut(self):
        if hasattr(self, 'delete_item'):
            selected = self.table.selectionModel().selectedRows()
            if not selected:
                show_toast("الرجاء تحديد صف للحذف", "warning", self)
                return
            row = selected[0].row()
            item_id = self.model.get_id(row)
            name = self.get_item_name_from_row(row) if hasattr(self, 'get_item_name_from_row') else str(item_id)
            reply = QMessageBox.question(self, "تأكيد الحذف", f"هل تريد حذف '{name}'؟",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.delete_item(item_id)
                    show_toast("تم الحذف", "success", self)
                    self.refresh()
                except Exception as e:
                    show_toast(str(e), "error", self)

    def _on_refresh_shortcut(self):
        if hasattr(self, 'refresh'):
            self.refresh()

    def _on_print_shortcut(self):
        if hasattr(self, 'print_table'):
            self.print_table()

    def _on_export_shortcut(self):
        if hasattr(self, 'export_to_excel'):
            self.export_to_excel()

    def _on_double_click(self, index):
        if hasattr(self, 'edit_item'):
            self.edit_item(index)

    def _show_context_menu(self, pos):
        menu = QMenu()
        if hasattr(self, 'add_item'):
            a = QAction(qta.icon('fa5s.plus'), "إضافة", self)
            a.triggered.connect(self.add_item)
            menu.addAction(a)
        if hasattr(self, 'edit_item'):
            a = QAction(qta.icon('fa5s.edit'), "تعديل", self)
            a.triggered.connect(self._on_edit_shortcut)
            menu.addAction(a)
        if hasattr(self, 'delete_item'):
            a = QAction(qta.icon('fa5s.trash-alt'), "حذف", self)
            a.triggered.connect(self._on_delete_shortcut)
            menu.addAction(a)
        menu.addSeparator()
        if hasattr(self, 'export_to_excel'):
            a = QAction(qta.icon('fa5s.file-excel'), "Excel", self)
            a.triggered.connect(self.export_to_excel)
            menu.addAction(a)
        if hasattr(self, 'print_table'):
            a = QAction(qta.icon('fa5s.print'), "طباعة", self)
            a.triggered.connect(self.print_table)
            menu.addAction(a)
        if menu.actions():
            menu.exec_(self.table.viewport().mapToGlobal(pos))


