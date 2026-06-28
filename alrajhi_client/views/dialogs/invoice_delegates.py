# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox, QDoubleSpinBox, QLineEdit, QCompleter
from PyQt5.QtCore import Qt, QStringListModel
from decimal import Decimal

def _decimal_value(value, default='0'):
    try:
        if isinstance(value, Decimal):
            return value
        if value is None or value == '':
            return Decimal(str(default))
        return Decimal(str(value))
    except Exception:
        return Decimal(str(default))

def _positive_decimal(value, default='1'):
    result = _decimal_value(value, default)
    return result if result > 0 else Decimal(str(default))


def _text_key(value):
    return str(value or '').strip().casefold()


def _item_matches_text(item, text):
    needle = _text_key(text)
    if not needle:
        return False
    return any(_text_key(item.get(key)) == needle for key in ('name', 'item_name', 'product_name', 'barcode', 'code'))


class ItemComboDelegate(QStyledItemDelegate):
    def __init__(self, items_list, parent=None):
        super().__init__(parent)
        self.items = items_list

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(True)
        try:
            combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        for item in self.items:
            combo.addItem(item.get('name') or item.get('item_name') or '', item)
        completer = QCompleter()
        terms = []
        seen = set()
        for item in self.items:
            for value in (item.get('name'), item.get('item_name'), item.get('barcode'), item.get('code')):
                text = str(value or '').strip()
                key = text.casefold()
                if text and key not in seen:
                    seen.add(key)
                    terms.append(text)
        model = QStringListModel(terms)
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        try:
            completer.setFilterMode(Qt.MatchContains)
        except Exception:
            pass
        combo.setCompleter(completer)
        # Phase412: currentIndexChanged also fires while the delegate is only
        # loading editor data.  Emitting commitData from that signal can overwrite
        # the line before the operator confirms the cell.  Commit through the
        # normal delegate close/Enter path instead.
        try:
            combo.activated.connect(lambda _index=None: self.commitData.emit(combo))
        except Exception:
            pass
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        current_key = _text_key(value)
        idx = -1
        for i in range(editor.count()):
            if _text_key(editor.itemText(i)) == current_key:
                idx = i
                break
        if idx >= 0:
            editor.setCurrentIndex(idx)
        else:
            editor.setEditText(str(value or ''))

    def setModelData(self, editor, model, index):
        current_text = editor.currentText()
        item_data = editor.currentData()
        if not item_data:
            for it in self.items:
                if _item_matches_text(it, current_text):
                    item_data = it
                    break
        if item_data:
            model.set_item(index.row(), item_data['id'], item_data.get('name') or item_data.get('item_name') or '',
                           item_data.get('units_list', []), item_data.get('price', 0), item_data.get('barcode', ''))
        else:
            model.setData(index, current_text, Qt.EditRole)

class UnitComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(False)
        return combo

    def setEditorData(self, editor, index):
        model = index.model()
        row = index.row()
        units_data = model.lines[row].get('units_data', [])
        editor.clear()
        current_display = model.data(index, Qt.EditRole)
        current_index = 0
        for i, u in enumerate(units_data):
            editor.addItem(u['unit_name'], (u['id'], u['unit_name'], u['conversion_factor']))
            if u['unit_name'] == current_display:
                current_index = i
        editor.setCurrentIndex(current_index)

    def setModelData(self, editor, model, index):
        selected_data = editor.currentData()
        if selected_data:
            row = index.row()
            old_factor = _positive_decimal(model.lines[row].get('conversion_factor', Decimal('1')), '1')
            new_factor = _positive_decimal(selected_data[2], '1')
            old_price = _decimal_value(model.lines[row].get('price', 0), '0')
            # تحديث الوحدة وعامل التحويل في النموذج أولاً.
            model.setData(index, (selected_data[0], selected_data[1], new_factor), Qt.EditRole)
            # سعر السطر هو سعر الوحدة المعروضة، لذلك عند التحويل من قطعة إلى كرتون
            # يجب أن يتغير السعر والإجمالي بنسبة عامل التحويل.
            if old_factor != new_factor and old_factor > 0:
                new_price = old_price * (new_factor / old_factor)
                price_col = getattr(model, 'COL_PRICE', 5)
                model.setData(model.index(row, price_col), new_price, Qt.EditRole)
            else:
                model.update_row_total(row)

class DoubleSpinDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        spin = QDoubleSpinBox(parent)
        spin.setRange(0, 999999999)
        spin.setDecimals(2)
        return spin

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setValue(float(value))

    def setModelData(self, editor, model, index):
        model.setData(index, Decimal(str(editor.value())), Qt.EditRole)
        model.update_row_total(index.row())


