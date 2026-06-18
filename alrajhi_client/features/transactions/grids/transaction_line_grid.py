from __future__ import annotations

try:
    from ui.smart_table_view import SmartTableView
except Exception:
    from PyQt5.QtWidgets import QTableView as SmartTableView

from PyQt5.QtWidgets import QHeaderView

from .transaction_column_presets import DEFAULT_PRESET, visible_keys_for_preset
from .transaction_unit_delegate import TransactionUnitDelegate
from .transaction_item_delegate import TransactionItemDelegate


class TransactionLineGrid(SmartTableView):
    """Professional transaction line grid driven by a column schema.

    It keeps the ERP rule that required business columns cannot be hidden while
    still allowing the standard SmartTableView column chooser, reorder, density,
    and preset workflow.
    """

    def __init__(self, columns=None, parent=None, identity: str | None = None):
        try:
            super().__init__(parent, identity=identity)
        except TypeError:
            super().__init__(parent)
        self.columns_schema = columns or []
        self.required_keys = {c.key for c in self.columns_schema if getattr(c, "required", False)}
        self._items_provider = None
        self._price_key_provider = None
        self._availability_provider = None
        self._item_transform = None
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        try:
            self.horizontalHeader().setSectionsMovable(True)
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.verticalHeader().setVisible(False)
            self.setSelectionBehavior(self.SelectRows)
            self.setSelectionMode(self.SingleSelection)
        except Exception:
            pass

    def set_schema(self, columns) -> None:
        self.columns_schema = columns or []
        self.required_keys = {c.key for c in self.columns_schema if getattr(c, "required", False)}
        self.apply_default_visibility()
        self.install_schema_delegates()

    def setModel(self, model):  # type: ignore[override]
        super().setModel(model)
        if not self.columns_schema and hasattr(model, "columns"):
            self.set_schema(model.columns)
        else:
            self.apply_default_visibility()
        self.install_schema_delegates()

    def configure_item_delegate(self, *, items_provider=None, price_key_provider=None, availability_provider=None, item_transform=None) -> None:
        self._items_provider = items_provider
        self._price_key_provider = price_key_provider
        self._availability_provider = availability_provider
        self._item_transform = item_transform
        self.install_schema_delegates()

    def install_schema_delegates(self) -> None:
        item_col = self.column_index("item")
        if item_col >= 0:
            # Only invoice-like editable grids should get the item lookup editor.
            # POS, restaurant order grids, and return grids display material names
            # as resolved business facts; they must not open a material completer
            # from a read-only cell.
            try:
                item_column = self.columns_schema[item_col]
            except Exception:
                item_column = None
            if getattr(item_column, "editable", True):
                try:
                    self.setItemDelegateForColumn(
                        item_col,
                        TransactionItemDelegate(
                            self,
                            items_provider=self._items_provider,
                            price_key_provider=self._price_key_provider,
                            availability_provider=self._availability_provider,
                            item_transform=self._item_transform,
                        ),
                    )
                except Exception:
                    pass
        unit_col = self.column_index("unit")
        if unit_col >= 0:
            try:
                unit_column = self.columns_schema[unit_col]
            except Exception:
                unit_column = None
            if getattr(unit_column, "editable", True):
                try:
                    self.setItemDelegateForColumn(unit_col, TransactionUnitDelegate(self))
                except Exception:
                    pass

    def column_index(self, key: str) -> int:
        for index, column in enumerate(self.columns_schema):
            if column.key == key:
                return index
        return -1

    def visible_keys(self) -> list[str]:
        keys: list[str] = []
        for idx, column in enumerate(self.columns_schema):
            if not self.isColumnHidden(idx):
                keys.append(column.key)
        return keys

    def apply_visible_keys(self, keys) -> None:
        visible = set(keys or []) | self.required_keys
        for idx, col in enumerate(self.columns_schema):
            super().setColumnHidden(idx, col.key not in visible)
        self.fit_transaction_columns()

    def setColumnHidden(self, column, hide):  # type: ignore[override]
        if 0 <= column < len(self.columns_schema):
            if hide and self.columns_schema[column].key in self.required_keys:
                return
        super().setColumnHidden(column, hide)

    def set_column_visible(self, column, visible):  # type: ignore[override]
        if 0 <= column < len(self.columns_schema):
            if not visible and self.columns_schema[column].key in self.required_keys:
                return
        if hasattr(super(), "set_column_visible"):
            return super().set_column_visible(column, visible)
        return self.setColumnHidden(column, not visible)

    def apply_default_visibility(self) -> None:
        for idx, col in enumerate(self.columns_schema):
            super().setColumnHidden(idx, not getattr(col, "default_visible", True))
            try:
                self.setColumnWidth(idx, int(getattr(col, "width", 120) or 120))
            except Exception:
                pass
        self.fit_transaction_columns()

    def apply_named_preset(self, preset_name: str | None = None) -> None:
        keys = visible_keys_for_preset(preset_name or DEFAULT_PRESET, self.columns_schema)
        self.apply_visible_keys(keys)

    def apply_compact_preset(self) -> None:
        self.apply_named_preset("compact")

    def apply_wide_preset(self) -> None:
        self.apply_named_preset(DEFAULT_PRESET)

    def fit_transaction_columns(self) -> None:
        """Keep the item column dominant while preserving operator-resizable columns."""
        try:
            header = self.horizontalHeader()
            for idx, col in enumerate(self.columns_schema):
                if self.isColumnHidden(idx):
                    continue
                if getattr(col, "stretch", False):
                    header.setSectionResizeMode(idx, QHeaderView.Stretch)
                else:
                    header.setSectionResizeMode(idx, QHeaderView.Interactive)
                    width = int(getattr(col, "width", 120) or 120)
                    if self.columnWidth(idx) < min(width, 80):
                        self.setColumnWidth(idx, width)
        except Exception:
            pass
