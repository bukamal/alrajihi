from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Dict, Any, Optional
from PyQt5.QtGui import QColor, QBrush
from i18n.translator import translate_text

class GenericTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict], headers: List[str], key_fields: List[str] = None, data_keys: List[str] = None):
        super().__init__()
        self._data = data
        self._headers = headers
        self._key_fields = key_fields or []
        self._data_keys = data_keys if data_keys is not None else headers
        if len(self._data_keys) < len(self._headers):
            self._data_keys.extend([''] * (len(self._headers) - len(self._data_keys)))

    def _value_at(self, record, key, col=None, default=''):
        """Return a cell value from dict rows or sequence rows.

        Some legacy pages still pass list/tuple rows to GenericTableModel,
        while newer pages pass dict rows. Supporting both keeps all existing
        screens compatible after the UI unification patches.
        """
        if isinstance(record, dict):
            return record.get(key, default)
        if isinstance(record, (list, tuple)):
            # Prefer an explicit numeric key when supplied, otherwise use column index.
            idx = None
            if isinstance(key, int):
                idx = key
            else:
                try:
                    idx = int(key)
                except Exception:
                    idx = col
            if idx is not None and 0 <= idx < len(record):
                return record[idx]
        return default

    def _set_value_at(self, row_index, key, col, value):
        record = self._data[row_index]
        if isinstance(record, dict):
            record[key] = value
            return True
        if isinstance(record, list):
            idx = None
            if isinstance(key, int):
                idx = key
            else:
                try:
                    idx = int(key)
                except Exception:
                    idx = col
            if idx is not None and 0 <= idx < len(record):
                record[idx] = value
                return True
        return False

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row >= len(self._data):
            return None
        record = self._data[row]

        if role == Qt.BackgroundRole:
            severity = self._value_at(record, '_severity') or self._value_at(record, '_row_status')
            if severity in ('out', 'critical'):
                return QBrush(QColor(255, 230, 230))
            if severity in ('low', 'warning'):
                return QBrush(QColor(255, 245, 220))
            return None

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role == Qt.ToolTipRole:
            if col < len(self._data_keys):
                key = self._data_keys[col]
                value = self._value_at(record, key, col, '')
                return str(value) if value is not None else ''
            return None

        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        if col >= len(self._data_keys):
            return None
        key = self._data_keys[col]
        value = self._value_at(record, key, col, '')
        return str(value) if value is not None else ''

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        row = index.row()
        col = index.column()
        if row >= len(self._data) or col >= len(self._data_keys):
            return False
        key = self._data_keys[col]
        if not self._set_value_at(row, key, col, value):
            return False
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return translate_text(self._headers[section])
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def sort(self, column: int, order=Qt.AscendingOrder):
        if column < 0 or column >= len(self._data_keys):
            return
        key = self._data_keys[column]
        if not key:
            return

        def sort_key(row):
            value = self._value_at(row, key, column, '')
            if value is None:
                return ''
            # Try numeric sort first, then fallback to case-insensitive text.
            try:
                return float(str(value).replace(',', '').replace(' ', ''))
            except Exception:
                return str(value).lower()

        self.layoutAboutToBeChanged.emit()
        self._data.sort(key=sort_key, reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

    def refresh_data(self, new_data: List[Dict]):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

    def get_row(self, row: int) -> Dict:
        if 0 <= row < len(self._data):
            return self._data[row]
        return {}

    def get_id(self, row: int) -> Any:
        if self._key_fields and row < len(self._data):
            return self._value_at(self._data[row], self._key_fields[0], 0, None)
        return None


