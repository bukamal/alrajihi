# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableView, QMenu, QAction, QFileDialog, QMessageBox, QApplication, QHeaderView, QStyledItemDelegate
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QKeySequence, QTextDocument, QFont
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from theme_manager import ThemeManager
from views.widgets.components.table_preferences import TablePreferences
import re
import html as _html

class CenterAlignDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignCenter
        super().paint(painter, option, index)

class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        self._restoring_layout = False
        self._layout_save_pending = False
        self._preferences = TablePreferences()
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().sectionResized.connect(self._schedule_save_layout)
        self.horizontalHeader().sectionMoved.connect(lambda *args: self._schedule_save_layout())

        self.setItemDelegate(CenterAlignDelegate(self))

        self.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.verticalHeader().setDefaultAlignment(Qt.AlignCenter)

        self.copy_action = QAction(self)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.copy_action.triggered.connect(self.copy_selection)
        self.addAction(self.copy_action)

        self.refresh_style()

    def set_table_identity(self, identity: str):
        """Set a stable key used to persist column widths/order/visibility."""
        if identity:
            self.setObjectName(identity)
            self.restore_layout()

    def _layout_key(self) -> str:
        name = self.objectName() or self.__class__.__name__
        parent = self.parent()
        parent_name = parent.__class__.__name__ if parent is not None else 'root'
        return f"tables/{parent_name}/{name}"

    def _schedule_save_layout(self, *args):
        if self._restoring_layout:
            return
        if self._layout_save_pending:
            return
        self._layout_save_pending = True
        QTimer.singleShot(250, self.save_layout)

    def save_layout(self):
        self._layout_save_pending = False
        if not self.model():
            return
        self._preferences.save_state(self._layout_key(), self.horizontalHeader().saveState())

    def restore_layout(self):
        if not self.model():
            return
        state = self._preferences.load_state(self._layout_key())
        if state:
            self._restoring_layout = True
            try:
                self.horizontalHeader().restoreState(state)
            finally:
                self._restoring_layout = False

    def reset_layout(self):
        self._preferences.reset(self._layout_key())
        self._restoring_layout = True
        try:
            for col in range(self.model().columnCount() if self.model() else 0):
                self.setColumnHidden(col, False)
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        finally:
            self._restoring_layout = False
        self.save_layout()

    def setModel(self, model):
        super().setModel(model)
        self.restore_layout()

    def copy_selection(self):
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return
        rows = sorted(set(i.row() for i in selection))
        cols = sorted(set(i.column() for i in selection))
        text = ""
        for r in rows:
            row_data = []
            for c in cols:
                idx = self.model().index(r, c)
                data = self.model().data(idx, Qt.DisplayRole)
                row_data.append(str(data))
            text += "\t".join(row_data) + "\n"
        QApplication.clipboard().setText(text)

    def _show_menu(self, pos):
        menu = QMenu()
        export_excel = QAction("📊 تصدير إلى Excel", self)
        export_excel.triggered.connect(self.export_to_excel)
        menu.addAction(export_excel)
        export_pdf = QAction("📄 طباعة", self)
        export_pdf.triggered.connect(self.print_table)
        menu.addAction(export_pdf)
        menu.addSeparator()
        copy_act = QAction("📋 نسخ", self)
        copy_act.triggered.connect(self.copy_selection)
        menu.addAction(copy_act)

        model = self.model()
        if model:
            columns_menu = menu.addMenu("🧩 الأعمدة")
            for col in range(model.columnCount()):
                header = model.headerData(col, Qt.Horizontal, Qt.DisplayRole) or f"عمود {col + 1}"
                action = QAction(str(header), self)
                action.setCheckable(True)
                action.setChecked(not self.isColumnHidden(col))
                action.toggled.connect(lambda checked, c=col: self.set_column_visible(c, checked))
                columns_menu.addAction(action)
            reset_columns = QAction("↩️ إعادة ضبط الأعمدة", self)
            reset_columns.triggered.connect(self.reset_layout)
            columns_menu.addSeparator()
            columns_menu.addAction(reset_columns)
        menu.exec(self.viewport().mapToGlobal(pos))

    def set_column_visible(self, column, visible):
        self.setColumnHidden(column, not visible)
        self.save_layout()

    def _set_column_visible(self, column, visible):
        self.set_column_visible(column, visible)

    def export_to_excel(self):
        model = self.model()
        if not model:
            return
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment
        except ImportError:
            QMessageBox.warning(self, "تنبيه", "مكتبة openpyxl غير مثبتة")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "حفظ التقرير", "report.xlsx", "Excel (*.xlsx)")
        if not filename:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "تقرير"
        visible_cols = [col for col in range(model.columnCount()) if not self.isColumnHidden(col)]
        for out_col, col in enumerate(visible_cols, start=1):
            header = model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            cell = ws.cell(row=1, column=out_col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(model.rowCount()):
            for out_col, col in enumerate(visible_cols, start=1):
                idx = model.index(row, col)
                value = model.data(idx, Qt.DisplayRole)
                ws.cell(row=row+2, column=out_col, value=value)
        wb.save(filename)
        QMessageBox.information(self, "نجاح", f"تم التصدير إلى {filename}")

    def print_table(self):
        model = self.model()
        if not model:
            return
        visible_cols = [col for col in range(model.columnCount()) if not self.isColumnHidden(col)]
        headers = []
        for col in visible_cols:
            h = model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
            headers.append(str(h) if h else f"عمود{col+1}")
        data = []
        for row in range(model.rowCount()):
            row_data = []
            for col in visible_cols:
                idx = model.index(row, col)
                val = model.data(idx, Qt.DisplayRole)
                row_data.append(str(val) if val is not None else '')
            data.append(row_data)
        
        html = f'''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"><title>طباعة الجدول</title>
<style>
    body {{ font-family: 'Tajawal', 'Segoe UI', Tahoma, Arial; direction: rtl; background: white; margin: 1.5cm; }}
    table {{ width: 100%; border-collapse: collapse; direction: rtl; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; text-align: center; }}
    th {{ background: #f1f5f9; }}
</style>
</head>
<body>
<table>
    <thead><tr>{''.join(f'<th>{_html.escape(h)}</th>' for h in headers)}</tr></thead>
    <tbody>
'''
        for row in data:
            html += '<tr>' + ''.join(f'<td>{_html.escape(str(cell))}</td>' for cell in row) + '</tr>'
        html += '''
    </tbody>
</table>
</body>
</html>'''
        doc = QTextDocument()
        doc.setHtml(html)
        doc.setDefaultFont(QFont("Tajawal", 10))
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(lambda p: doc.print(p))
        preview.exec()

    def refresh_style(self):
        self.setStyleSheet(ThemeManager.get_stylesheet())
        self.viewport().update()

    def showEvent(self, event):
        self.refresh_style()
        super().showEvent(event)


