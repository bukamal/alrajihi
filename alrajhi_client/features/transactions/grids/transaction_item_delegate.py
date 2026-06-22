from __future__ import annotations

from typing import Any, Callable

from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtWidgets import QCompleter, QLineEdit, QStyledItemDelegate

from core.services.barcode_input_service import barcode_input_service
from core.services.catalog_service import catalog_service


class TransactionItemDelegate(QStyledItemDelegate):
    """Case-insensitive material editor for transaction line grids.

    The legacy quick-search field already supports case-insensitive material
    lookup.  This delegate brings the same behaviour to the *item cell itself*
    in sales/purchase invoice grids: typing ``milk`` can resolve ``Milk`` and
    selecting a unit barcode keeps the matched unit/conversion metadata.
    """

    def __init__(
        self,
        parent=None,
        *,
        items_provider: Callable[[str | None, int], list[dict[str, Any]]] | None = None,
        price_key_provider: Callable[[], str] | None = None,
        availability_provider: Callable[[dict[str, Any]], Any] | None = None,
        item_transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        super().__init__(parent)
        self.items_provider = items_provider
        self.price_key_provider = price_key_provider
        self.availability_provider = availability_provider
        self.item_transform = item_transform

    def _items(self, search: str | None = None, limit: int = 60) -> list[dict[str, Any]]:
        try:
            if self.items_provider:
                return self.items_provider(search, limit) or []
            return catalog_service.items(search=search or None, limit=limit) or []
        except Exception:
            return []

    def _terms_for_rows(self, rows: list[dict[str, Any]]) -> list[str]:
        seen: set[str] = set()
        terms: list[str] = []
        for row in rows or []:
            for value in (
                row.get("lookup_label"),
                row.get("search_label"),
                row.get("name"),
                row.get("item_name"),
                row.get("barcode"),
                row.get("code"),
                row.get("matched_barcode"),
            ):
                text = str(value or "").strip()
                key = text.casefold()
                if text and key not in seen:
                    seen.add(key)
                    terms.append(text)
        return terms

    def _row_for_text(self, text: str) -> dict[str, Any] | None:
        needle = str(text or "").strip().casefold()
        if not needle:
            return None
        for row in self._items(text, 80):
            for value in (
                row.get("lookup_label"),
                row.get("search_label"),
                row.get("matched_barcode"),
                row.get("barcode"),
                row.get("code"),
                row.get("variant"),
            ):
                if str(value or "").strip().casefold() == needle:
                    return dict(row)
        return None

    def _refresh_completer(self, editor: QLineEdit, text: str) -> None:
        model = getattr(editor, "_transaction_item_completer_model", None)
        if model is None:
            return
        normalized = barcode_input_service.normalize(text)
        if normalized and barcode_input_service.looks_like_scan(normalized):
            model.setStringList([])
            return
        rows = self._items(text.strip() or None, 60)
        model.setStringList(self._terms_for_rows(rows))

    def createEditor(self, parent, option, index):  # type: ignore[override]
        editor = QLineEdit(parent)
        completer_model = QStringListModel(editor)
        completer = QCompleter(completer_model, editor)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        try:
            completer.setFilterMode(Qt.MatchContains)
        except Exception:
            pass
        completer.setCompletionMode(QCompleter.PopupCompletion)
        editor.setCompleter(completer)
        editor._transaction_item_completer_model = completer_model  # type: ignore[attr-defined]
        editor.textEdited.connect(lambda text: self._refresh_completer(editor, text))
        self._refresh_completer(editor, "")
        return editor

    def setEditorData(self, editor, index):  # type: ignore[override]
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value or ""))
        editor.selectAll()
        self._refresh_completer(editor, editor.text())

    def setModelData(self, editor, model, index):  # type: ignore[override]
        text = str(editor.text() or "").strip()
        if not text:
            model.setData(index, "", Qt.EditRole)
            return
        item = self._row_for_text(text)
        if not item:
            try:
                lookup = barcode_input_service.lookup_entry(text, mode="auto")
            except Exception:
                lookup = None
            item = getattr(lookup, "item", None) if lookup is not None else None
        if item and hasattr(model, "set_item"):
            if self.item_transform:
                try:
                    transformed = self.item_transform(item)
                    if not transformed:
                        item = None
                    else:
                        item = transformed
                except Exception:
                    item = None
            if not item:
                model.setData(index, text, Qt.EditRole)
                return
            price_key = self.price_key_provider() if self.price_key_provider else "selling_price"
            try:
                available = self.availability_provider(item) if self.availability_provider else None
            except Exception:
                available = None
            if model.set_item(index.row(), item, price_key=price_key, warehouse_available=available):
                return
        # Keep the typed text visible if it did not resolve, but do not invent an
        # item_id.  Save validation will still ignore unresolved lines.
        model.setData(index, text, Qt.EditRole)
