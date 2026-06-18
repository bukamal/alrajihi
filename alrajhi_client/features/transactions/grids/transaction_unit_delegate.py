from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate


class TransactionUnitDelegate(QStyledItemDelegate):
    """Text-first unit editor for TransactionLineGrid.

    The cell is painted as plain table text.  A QComboBox is created only while
    the user edits the unit cell, avoiding the old always-visible cell-widget
    pattern used by the legacy return dialogs.  The delegate delegates all
    business updates to TransactionLineModel.set_unit(), so conversion_factor,
    unit_id, display quantities, unit price and row total stay consistent.
    """

    def createEditor(self, parent, option, index):  # type: ignore[override]
        combo = QComboBox(parent)
        combo.setEditable(False)
        model = index.model()
        options = []
        if hasattr(model, "unit_options_for_row"):
            options = model.unit_options_for_row(index.row())
        for unit in options or []:
            combo.addItem(str(unit.get("unit_name") or unit.get("unit") or ""), unit)
        if combo.count() == 0:
            combo.addItem(str(index.data(Qt.EditRole) or ""), {
                "unit_name": str(index.data(Qt.EditRole) or ""),
                "unit_id": None,
                "conversion_factor": "1",
            })
        return combo

    def setEditorData(self, editor, index):  # type: ignore[override]
        current = str(index.data(Qt.EditRole) or "")
        current_unit_id = None
        try:
            row_data = index.model().lines[index.row()]
            current_unit_id = row_data.get("unit_id")
        except Exception:
            pass
        selected = -1
        for i in range(editor.count()):
            data = editor.itemData(i) or {}
            if current_unit_id not in (None, "") and str(data.get("unit_id")) == str(current_unit_id):
                selected = i
                break
            if str(data.get("unit_name") or data.get("unit") or editor.itemText(i)) == current:
                selected = i
        editor.setCurrentIndex(selected if selected >= 0 else 0)

    def setModelData(self, editor, model, index):  # type: ignore[override]
        data = dict(editor.currentData() or {})
        if not data:
            data = {
                "unit_name": editor.currentText(),
                "unit_id": None,
                "conversion_factor": "1",
            }
        if hasattr(model, "set_unit"):
            model.set_unit(index.row(), data)
        else:
            model.setData(index, editor.currentText(), Qt.EditRole)
