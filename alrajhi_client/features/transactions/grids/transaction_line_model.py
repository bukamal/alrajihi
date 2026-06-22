from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.services.product_service import product_service
from ..i18n import tr
from core.money_display_policy import policy_for

from .transaction_column_schema import TransactionColumn


class TransactionLineModel(QAbstractTableModel):
    """Schema-driven line model for invoices and returns.

    Phase 167 adds return workflow helpers and stricter base-quantity validation on top of unit-aware editing.  The
    model now owns the unit conversion rules previously embedded in legacy
    return widgets: unit_id, conversion_factor, display quantities, base
    quantities, unit price and row totals are updated atomically.
    """

    NUMERIC_KEYS = {
        "qty", "price", "cost", "discount", "tax", "available", "total",
        "original_qty", "previous_qty", "returnable_qty",
    }

    def __init__(self, columns: list[TransactionColumn], parent=None):
        super().__init__(parent)
        self.columns = columns
        self.lines: list[dict[str, Any]] = []

    def rowCount(self, parent=QModelIndex()):  # type: ignore[override]
        return 0 if parent.isValid() else len(self.lines)

    def columnCount(self, parent=QModelIndex()):  # type: ignore[override]
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.columns):
            return self.columns[section].title
        return section + 1

    def _value(self, row: int, col: int):
        key = self.columns[col].key
        data = self.lines[row]
        if key == "row":
            return row + 1
        return data.get(key, "")

    def data(self, index, role=Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        col = self.columns[index.column()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            value = self._value(index.row(), index.column())
            if role == Qt.DisplayRole and getattr(col, "numeric", False) and value not in (None, ""):
                try:
                    policy = policy_for()
                    if col.key in {"price", "cost", "discount", "tax", "total"}:
                        return policy.format_money(value)
                    return policy.format_quantity(value)
                except Exception:
                    try:
                        d = Decimal(str(value))
                        if d == d.to_integral_value() and col.key in {"qty", "original_qty", "previous_qty", "returnable_qty"}:
                            return f"{d:.0f}"
                        return f"{d:.2f}"
                    except Exception:
                        return value
            return value
        if role == Qt.TextAlignmentRole and col.numeric:
            return Qt.AlignRight | Qt.AlignVCenter
        return None

    def flags(self, index):  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self.columns[index.column()].editable:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.EditRole):  # type: ignore[override]
        if role != Qt.EditRole or not index.isValid():
            return False
        key = self.columns[index.column()].key
        if key == "row":
            return False
        if key == "unit":
            if isinstance(value, dict):
                return self.set_unit(index.row(), value)
            self.lines[index.row()][key] = str(value or "")
            self._emit_row_changed(index.row())
            return True
        if key in self.NUMERIC_KEYS:
            value = self._decimal(value)
            if key == "qty":
                value = self._clamp_qty_for_row(index.row(), value)
        self.lines[index.row()][key] = value
        self._recalculate_row(index.row())
        self._emit_row_changed(index.row())
        return True

    def _emit_row_changed(self, row_index: int) -> None:
        if 0 <= row_index < len(self.lines):
            self.dataChanged.emit(
                self.index(row_index, 0),
                self.index(row_index, len(self.columns) - 1),
                [Qt.DisplayRole, Qt.EditRole],
            )

    def _empty_line(self) -> dict[str, Any]:
        row = {col.key: "" for col in self.columns}
        row.update({
            "item_id": None,
            "unit_id": None,
            "unit_options": [],
            "conversion_factor": Decimal("1"),
            "base_unit_price": Decimal("0"),
            "qty": Decimal("0"),
            "price": Decimal("0"),
            "cost": Decimal("0"),
            "discount": Decimal("0"),
            "tax": Decimal("0"),
            "total": Decimal("0"),
            "original_invoice_line_id": None,
            "quantity_in_base": None,
            "original_qty_base": None,
            "previous_qty_base": None,
            "returnable_qty_base": None,
            "returnable_qty": row.get("returnable_qty", ""),
            "restock": row.get("restock", tr("yes")),
        })
        return row

    def add_empty_line(self) -> int:
        row_index = len(self.lines)
        self.beginInsertRows(QModelIndex(), row_index, row_index)
        self.lines.append(self._empty_line())
        self.endInsertRows()
        return row_index

    def clear(self, keep_empty: bool = True) -> None:
        self.beginResetModel()
        self.lines = []
        self.endResetModel()
        if keep_empty:
            self.add_empty_line()

    def fill_return_quantities_to_max(self) -> int:
        """Set each return row quantity to the remaining returnable display quantity."""
        changed = 0
        for row_index, row in enumerate(self.lines):
            if not row.get("item_id") or not row.get("original_invoice_line_id"):
                continue
            max_qty = self._decimal(row.get("returnable_qty"))
            if max_qty <= 0:
                continue
            if self._decimal(row.get("qty")) != max_qty:
                row["qty"] = max_qty
                self._recalculate_row_data(row)
                changed += 1
        if changed:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.lines) - 1, len(self.columns) - 1), [Qt.DisplayRole, Qt.EditRole])
        return changed

    def clear_return_quantities(self) -> int:
        """Reset entered return quantities without dropping the invoice line context."""
        changed = 0
        for row_index, row in enumerate(self.lines):
            if self._decimal(row.get("qty")) != 0:
                row["qty"] = Decimal("0")
                self._recalculate_row_data(row)
                changed += 1
        if changed:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.lines) - 1, len(self.columns) - 1), [Qt.DisplayRole, Qt.EditRole])
        return changed

    def return_summary(self) -> dict[str, Decimal]:
        selected_qty = Decimal("0")
        returnable_qty = Decimal("0")
        selected_base = Decimal("0")
        returnable_base = Decimal("0")
        for row in self.lines:
            if not row.get("item_id") or not row.get("original_invoice_line_id"):
                continue
            selected_qty += self._decimal(row.get("qty"))
            returnable_qty += self._decimal(row.get("returnable_qty"))
            factor = self._positive_decimal(row.get("conversion_factor") or 1)
            selected_base += self._decimal(row.get("qty")) * factor
            returnable_base += self._decimal(row.get("returnable_qty_base"), str(self._decimal(row.get("returnable_qty")) * factor))
        return {
            "selected_qty": selected_qty,
            "returnable_qty": returnable_qty,
            "selected_base": selected_base,
            "returnable_base": returnable_base,
            "selected_total": self.total_amount(),
        }

    def return_validation_errors(self) -> list[str]:
        """Validate return quantities in base units to survive unit changes."""
        errors: list[str] = []
        seen_original_lines = set()
        for row_number, row in enumerate(self.lines, start=1):
            if not row.get("item_id") and self._decimal(row.get("qty")) <= 0:
                continue
            original_line_id = row.get("original_invoice_line_id")
            if row.get("item_id") and not original_line_id:
                errors.append(tr("transaction_return_line_missing_original", row=row_number))
                continue
            if original_line_id in seen_original_lines:
                errors.append(tr("transaction_return_line_duplicate_original", row=row_number))
            seen_original_lines.add(original_line_id)
            qty = self._decimal(row.get("qty"))
            if qty < 0:
                errors.append(tr("transaction_return_line_negative_qty", row=row_number))
                continue
            if qty == 0:
                continue
            factor = self._positive_decimal(row.get("conversion_factor") or 1)
            base_qty = qty * factor
            max_base = row.get("returnable_qty_base")
            if max_base in (None, ""):
                max_base = self._decimal(row.get("returnable_qty")) * factor
            else:
                max_base = self._decimal(max_base)
            if max_base < 0:
                max_base = Decimal("0")
            if base_qty > max_base:
                item = row.get("item") or row.get("barcode") or original_line_id
                errors.append(tr("transaction_return_line_qty_exceeds", row=row_number, item=item))
        return errors

    def _variant_info(self, item: dict[str, Any] | None) -> dict[str, Any]:
        item = item or {}
        matched = item.get("matched_variant") or {}
        if not isinstance(matched, dict):
            matched = {}
        variant_id = matched.get("variant_id") or matched.get("id") or item.get("variant_id")
        color = matched.get("color") or item.get("variant_color") or ""
        size = matched.get("size") or item.get("variant_size") or ""
        sku = matched.get("sku") or item.get("variant_sku") or ""
        label = " / ".join(str(v).strip() for v in (color, size) if str(v or "").strip())
        return {
            "variant_id": variant_id,
            "variant_color": str(color or ""),
            "variant_size": str(size or ""),
            "variant_sku": str(sku or ""),
            "variant": label,
        }

    def set_item(self, row_index: int, item: dict[str, Any], price_key: str = "selling_price", qty=None, warehouse_available=None) -> bool:
        """Resolve a material into an existing line.

        This is used by the professional item-cell delegate.  It intentionally
        shares the same unit/barcode/price logic as add_item(), so selecting a
        material from the grid cell behaves exactly like scanning or using the
        quick-search field.
        """
        if not item or not (0 <= row_index < len(self.lines)):
            return False
        matched_unit = item.get("matched_unit") or {}
        factor = self._positive_decimal(
            matched_unit.get("conversion_factor")
            or item.get("conversion_factor")
            or item.get("factor")
            or 1
        )
        explicit_price = item.get("unit_price") if item.get("unit_price") not in (None, "") else item.get("price")
        base_price = self._decimal(item.get("base_unit_price") or item.get(price_key) or item.get("selling_price") or item.get("purchase_price") or 0)
        price = self._decimal(explicit_price) if explicit_price not in (None, "") else self._money(base_price * factor)
        unit = matched_unit.get("unit_name") or matched_unit.get("unit") or item.get("unit") or item.get("unit_name") or ""
        unit_id = matched_unit.get("unit_id") if matched_unit else item.get("unit_id")
        scanned_barcode = item.get("matched_barcode") or matched_unit.get("barcode") or item.get("barcode") or item.get("code") or ""
        variant_info = self._variant_info(item)
        barcode_scope = item.get("barcode_scope") or ("variant" if variant_info.get("variant_id") else ("unit" if matched_unit else "item"))
        unit_options = self._unit_options_for_item(item, unit, unit_id, factor)
        current_qty = self._decimal(self.lines[row_index].get("qty"))
        qty_value = self._decimal(qty) if qty is not None else (current_qty if current_qty > 0 else Decimal("1"))
        self.lines[row_index].update({
            "item_id": item.get("id"),
            "barcode": scanned_barcode,
            "item": item.get("name") or item.get("item_name") or "",
            "unit": unit,
            "unit_id": unit_id,
            "unit_options": unit_options,
            "conversion_factor": factor,
            "base_unit_price": base_price,
            "qty": qty_value,
            "price": price,
            "cost": price,
            "available": self._decimal(warehouse_available) if warehouse_available is not None else item.get("available", ""),
            "batch": item.get("batch") or "",
            "expiry": item.get("expiry") or "",
            "variant": variant_info.get("variant") or "",
            "variant_id": variant_info.get("variant_id"),
            "variant_color": variant_info.get("variant_color") or "",
            "variant_size": variant_info.get("variant_size") or "",
            "variant_sku": variant_info.get("variant_sku") or "",
            "barcode_scope": barcode_scope,
            "matched_barcode": scanned_barcode,
        })
        self._recalculate_row(row_index)
        self._emit_row_changed(row_index)
        return True

    def add_item(self, item: dict[str, Any], price_key: str = "selling_price", qty=1, warehouse_available=None) -> int:
        if not self.lines or any(self.lines[-1].get(key) for key in ("item_id", "item", "barcode")):
            self.add_empty_line()
        row_index = len(self.lines) - 1
        self.set_item(row_index, item, price_key=price_key, qty=qty, warehouse_available=warehouse_available)
        return row_index

    def load_invoice_lines(self, lines: list[dict[str, Any]] | None) -> None:
        self.beginResetModel()
        self.lines = []
        for line in lines or []:
            row = self._empty_line()
            qty = self._decimal(self._line_value(line, "quantity", self._line_value(line, "qty", 0)))
            factor = self._positive_decimal(self._line_value(line, "conversion_factor", 1) or 1)
            unit_price = self._decimal(self._line_value(line, "unit_price", self._line_value(line, "price", 0)))
            unit_cost = self._decimal(self._line_value(line, "unit_cost", self._line_value(line, "cost", unit_price)))
            unit = self._line_value(line, "unit", self._line_value(line, "unit_name", "")) or ""
            item_id = self._line_value(line, "item_id")
            row.update({
                "item_id": item_id,
                "barcode": self._line_value(line, "barcode", "") or "",
                "item": self._item_name(line),
                "variant": self._variant_label(line),
                "variant_id": self._line_value(line, "variant_id"),
                "variant_color": self._line_value(line, "variant_color", "") or "",
                "variant_size": self._line_value(line, "variant_size", "") or "",
                "variant_sku": self._line_value(line, "variant_sku", "") or "",
                "barcode_scope": self._line_value(line, "barcode_scope", "") or "",
                "matched_barcode": self._line_value(line, "matched_barcode", "") or self._line_value(line, "barcode", "") or "",
                "unit": unit,
                "unit_id": self._line_value(line, "unit_id"),
                "unit_options": self._unit_options_for_line(line, unit, self._line_value(line, "unit_id"), factor),
                "conversion_factor": factor,
                "base_unit_price": unit_price / factor if factor else unit_price,
                "qty": qty,
                "price": unit_price,
                "cost": unit_cost,
                "discount": self._decimal(self._line_value(line, "discount", 0) or 0),
                "tax": self._decimal(self._line_value(line, "tax", 0) or 0),
                "total": self._decimal(self._line_value(line, "total", qty * unit_price)),
                "notes": self._line_value(line, "description", self._line_value(line, "notes", "")) or "",
                "batch": self._line_value(line, "batch", "") or "",
                "expiry": self._line_value(line, "expiry", "") or "",
            })
            if self._line_value(line, "total") in (None, ""):
                self._recalculate_row_data(row)
            self.lines.append(row)
        self.endResetModel()
        if not self.lines:
            self.add_empty_line()

    def load_returnable_lines(self, lines: list[dict[str, Any]] | None, original_invoice_label: str = "", return_kind: str = "sale") -> None:
        """Load invoice lines that can still be returned with unit metadata."""
        self.beginResetModel()
        self.lines = []
        original_key = "purchased_qty" if return_kind == "purchase" else "sold_qty"
        original_base_key = "purchased_qty_base" if return_kind == "purchase" else "sold_qty_base"
        for line in lines or []:
            row = self._empty_line()
            factor = self._positive_decimal(self._line_value(line, "conversion_factor", 1) or 1)
            unit_price = self._decimal(
                self._line_value(line, "unit_price_usd", self._line_value(line, "unit_price", self._line_value(line, "price", 0)))
            )
            original_base = self._decimal(self._line_value(line, original_base_key, 0))
            original_qty = self._decimal(
                self._line_value(line, original_key, self._line_value(line, "original_qty", self._line_value(line, "quantity", 0)))
            )
            if original_base <= 0:
                original_base = original_qty * factor
            if original_qty <= 0 and factor > 0:
                original_qty = original_base / factor
            previous_base = self._decimal(self._line_value(line, "returned_qty_base", 0))
            previous_qty = self._decimal(self._line_value(line, "returned_qty", self._line_value(line, "previous_qty", 0)))
            if previous_base <= 0:
                previous_base = previous_qty * factor
            returnable_base = self._decimal(self._line_value(line, "returnable_qty_base", 0))
            if returnable_base <= 0:
                returnable_base = max(Decimal("0"), original_base - previous_base)
            returnable_qty = self._decimal(self._line_value(line, "returnable_qty", 0))
            if returnable_qty <= 0 and factor > 0:
                returnable_qty = returnable_base / factor
            unit = self._line_value(line, "unit", self._line_value(line, "unit_name", self._line_value(line, "base_unit", ""))) or ""
            unit_id = self._line_value(line, "unit_id")
            row.update({
                "original_invoice": original_invoice_label,
                "original_invoice_line_id": self._line_value(line, "id", self._line_value(line, "original_invoice_line_id")),
                "item_id": self._line_value(line, "item_id"),
                "barcode": self._line_value(line, "barcode", self._line_value(line, "item_barcode", "")) or "",
                "item": self._item_name(line),
                "variant": self._variant_label(line),
                "variant_id": self._line_value(line, "variant_id"),
                "variant_color": self._line_value(line, "variant_color", "") or "",
                "variant_size": self._line_value(line, "variant_size", "") or "",
                "variant_sku": self._line_value(line, "variant_sku", "") or "",
                "barcode_scope": self._line_value(line, "barcode_scope", "") or "",
                "matched_barcode": self._line_value(line, "matched_barcode", "") or self._line_value(line, "barcode", "") or "",
                "original_qty_base": original_base,
                "previous_qty_base": previous_base,
                "returnable_qty_base": returnable_base,
                "original_qty": original_qty,
                "previous_qty": previous_qty,
                "returnable_qty": returnable_qty,
                "unit": unit,
                "unit_id": unit_id,
                "unit_options": self._unit_options_for_line(line, unit, unit_id, factor),
                "conversion_factor": factor,
                "base_unit_price": unit_price / factor if factor else unit_price,
                "qty": Decimal("0"),
                "price": unit_price,
                "cost": unit_price,
                "total": Decimal("0"),
                "reason": "",
                "restock": "نعم" if return_kind == "sale" else "",
                "notes": self._line_value(line, "notes", self._line_value(line, "description", "")) or "",
            })
            self.lines.append(row)
        self.endResetModel()
        if not self.lines:
            self.add_empty_line()

    def load_return_lines(self, lines: list[dict[str, Any]] | None, return_record: dict[str, Any] | None = None) -> None:
        """Load stored return lines for edit mode."""
        return_record = return_record or {}
        label = return_record.get("invoice_reference") or return_record.get("return_no") or str(return_record.get("original_invoice_id") or "")
        self.beginResetModel()
        self.lines = []
        for line in lines or []:
            row = self._empty_line()
            qty = self._decimal(self._line_value(line, "quantity", self._line_value(line, "qty", 0)))
            factor = self._positive_decimal(self._line_value(line, "conversion_factor", 1) or 1)
            unit_price = self._decimal(self._line_value(line, "unit_price", self._line_value(line, "price", 0)))
            unit = self._line_value(line, "unit", self._line_value(line, "unit_name", self._line_value(line, "base_unit", ""))) or ""
            unit_id = self._line_value(line, "unit_id")
            quantity_in_base = self._decimal(self._line_value(line, "quantity_in_base", qty * factor))
            row.update({
                "original_invoice": label,
                "original_invoice_line_id": self._line_value(line, "original_invoice_line_id"),
                "item_id": self._line_value(line, "item_id"),
                "barcode": self._line_value(line, "barcode", self._line_value(line, "item_barcode", "")) or "",
                "item": self._item_name(line),
                "variant": self._variant_label(line),
                "variant_id": self._line_value(line, "variant_id"),
                "variant_color": self._line_value(line, "variant_color", "") or "",
                "variant_size": self._line_value(line, "variant_size", "") or "",
                "variant_sku": self._line_value(line, "variant_sku", "") or "",
                "barcode_scope": self._line_value(line, "barcode_scope", "") or "",
                "matched_barcode": self._line_value(line, "matched_barcode", "") or self._line_value(line, "barcode", "") or "",
                "original_qty": self._line_value(line, "original_qty", ""),
                "previous_qty": self._line_value(line, "previous_qty", ""),
                "returnable_qty": self._line_value(line, "returnable_qty", ""),
                "unit": unit,
                "unit_id": unit_id,
                "unit_options": self._unit_options_for_line(line, unit, unit_id, factor),
                "conversion_factor": factor,
                "base_unit_price": unit_price / factor if factor else unit_price,
                "quantity_in_base": quantity_in_base,
                "qty": qty,
                "price": unit_price,
                "cost": unit_price,
                "total": self._decimal(self._line_value(line, "total", qty * unit_price)),
                "reason": self._line_value(line, "reason", "") or "",
                "restock": self._line_value(line, "restock", "") or "",
                "notes": self._line_value(line, "notes", self._line_value(line, "description", "")) or "",
            })
            if self._line_value(line, "total") in (None, ""):
                self._recalculate_row_data(row)
            self.lines.append(row)
        self.endResetModel()
        if not self.lines:
            self.add_empty_line()

    def remove_line(self, row: int) -> None:
        if 0 <= row < len(self.lines):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.lines.pop(row)
            self.endRemoveRows()
        if not self.lines:
            self.add_empty_line()

    def unit_options_for_row(self, row: int) -> list[dict[str, Any]]:
        if not (0 <= row < len(self.lines)):
            return []
        line = self.lines[row]
        options = line.get("unit_options") or []
        if not options:
            options = self._unit_options_for_line(line, line.get("unit", ""), line.get("unit_id"), line.get("conversion_factor") or 1)
            line["unit_options"] = options
        return options

    def set_unit(self, row: int, unit_data: dict[str, Any]) -> bool:
        if not (0 <= row < len(self.lines)):
            return False
        line = self.lines[row]
        old_factor = self._positive_decimal(line.get("conversion_factor") or 1)
        new_factor = self._positive_decimal(
            unit_data.get("conversion_factor", unit_data.get("factor", unit_data.get("value", 1)))
        )
        unit_name = unit_data.get("unit_name") or unit_data.get("unit") or line.get("unit") or ""
        unit_id = unit_data.get("unit_id", unit_data.get("id"))
        line["unit"] = unit_name
        line["unit_id"] = unit_id
        line["conversion_factor"] = new_factor

        # Keep a canonical base price and derive the visible unit price from it.
        base_price = self._decimal(line.get("base_unit_price"))
        if base_price <= 0:
            visible_price = self._decimal(line.get("price") or line.get("cost"))
            base_price = visible_price / old_factor if old_factor else visible_price
        visible = self._money(base_price * new_factor)
        if self._has_column("price"):
            line["price"] = visible
        if self._has_column("cost"):
            line["cost"] = visible
        line["base_unit_price"] = base_price

        # Return documents store the legal limit in base units; displayed maxes
        # must follow the selected unit.
        for display_key, base_key in (
            ("original_qty", "original_qty_base"),
            ("previous_qty", "previous_qty_base"),
            ("returnable_qty", "returnable_qty_base"),
        ):
            base_value = line.get(base_key)
            if base_value not in (None, ""):
                line[display_key] = self._decimal(base_value) / new_factor

        line["qty"] = self._clamp_qty_for_row(row, self._decimal(line.get("qty")))
        self._recalculate_row(row)
        self._emit_row_changed(row)
        return True

    def _unit_options_for_item(self, item: dict[str, Any], unit: str = "", unit_id=None, factor=1) -> list[dict[str, Any]]:
        options = []
        base_name = item.get("unit") or item.get("base_unit") or unit or "قطعة"
        options.append({"unit_id": None, "id": None, "unit_name": str(base_name), "conversion_factor": Decimal("1")})
        if item.get("matched_unit"):
            self._append_unit_option(options, item.get("matched_unit"))
        for source in (item.get("units") or item.get("units_list") or []):
            self._append_unit_option(options, source)
        item_id = item.get("id") or item.get("item_id")
        if item_id:
            try:
                for source in product_service.item_units(int(item_id)) or []:
                    self._append_unit_option(options, source)
            except Exception:
                pass
        self._append_unit_option(options, {"id": unit_id, "unit_name": unit, "conversion_factor": factor})
        return options

    def _unit_options_for_line(self, line, unit: str = "", unit_id=None, factor=1) -> list[dict[str, Any]]:
        if isinstance(line, dict) and line.get("unit_options"):
            return [self._normalize_unit_option(u) for u in line.get("unit_options") or []]
        item_id = self._line_value(line, "item_id")
        item = {}
        if item_id:
            try:
                item = product_service.item_by_id(int(item_id)) or {}
            except Exception:
                item = {}
        item.update({
            "id": item_id,
            "unit": item.get("unit") or self._line_value(line, "base_unit", self._line_value(line, "unit_name", unit)) or unit,
            "units": self._line_value(line, "units", self._line_value(line, "units_list", [])) or [],
        })
        return self._unit_options_for_item(item, unit, unit_id, factor)

    def _append_unit_option(self, options: list[dict[str, Any]], source: dict[str, Any] | None) -> None:
        if not source:
            return
        opt = self._normalize_unit_option(source)
        name = str(opt.get("unit_name") or "").strip()
        if not name:
            return
        factor = self._positive_decimal(opt.get("conversion_factor") or 1)
        opt["conversion_factor"] = factor
        opt["factor"] = factor
        opt["unit"] = name
        for existing in options:
            same_id = opt.get("unit_id") not in (None, "") and str(existing.get("unit_id")) == str(opt.get("unit_id"))
            same_name = str(existing.get("unit_name") or "") == name
            if same_id or same_name:
                return
        options.append(opt)

    def _normalize_unit_option(self, source: dict[str, Any]) -> dict[str, Any]:
        unit_id = source.get("unit_id", source.get("id"))
        name = source.get("unit_name") or source.get("unit") or source.get("name") or ""
        factor = self._positive_decimal(source.get("conversion_factor", source.get("factor", 1)))
        barcode = source.get("barcode") or source.get("unit_barcode") or ""
        return {
            "unit_id": unit_id,
            "id": unit_id,
            "unit_name": str(name),
            "unit": str(name),
            "conversion_factor": factor,
            "factor": factor,
            "barcode": barcode,
            "unit_barcode": barcode,
            "notes": source.get("notes") or "",
        }

    def _clamp_qty_for_row(self, row_index: int, value: Decimal) -> Decimal:
        if value < 0:
            value = Decimal("0")
        if not (0 <= row_index < len(self.lines)):
            return value
        max_returnable = self.lines[row_index].get("returnable_qty")
        if max_returnable not in (None, ""):
            max_qty = self._decimal(max_returnable)
            if max_qty >= 0 and value > max_qty:
                value = max_qty
        return value

    def _decimal(self, value, default: str = "0") -> Decimal:
        try:
            if value is None or value == "":
                value = default
            return Decimal(str(value))
        except Exception:
            return Decimal(default)

    def _positive_decimal(self, value, default: str = "1") -> Decimal:
        result = self._decimal(value, default)
        return result if result > 0 else Decimal(default)

    def _money(self, value) -> Decimal:
        return self._decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _line_value(self, line, key, default=None):
        if isinstance(line, dict):
            return line.get(key, default)
        return getattr(line, key, default)

    def _item_name(self, line) -> str:
        for key in ("item_name", "name", "product_name", "description"):
            value = self._line_value(line, key)
            if value and not str(value).strip().isdigit():
                return str(value)
        item_id = self._line_value(line, "item_id")
        return f"#{item_id}" if item_id else ""

    def _variant_label(self, line) -> str:
        color = self._line_value(line, "variant_color", "") or ""
        size = self._line_value(line, "variant_size", "") or ""
        return " / ".join(str(v).strip() for v in (color, size) if str(v or "").strip())

    def _recalculate_row_data(self, row: dict[str, Any]) -> None:
        price = self._decimal(row.get("price")) or self._decimal(row.get("cost"))
        if self._has_column("cost") and not self._has_column("price"):
            price = self._decimal(row.get("cost"))
        subtotal = self._decimal(row.get("qty")) * price
        total = max(Decimal("0"), subtotal - self._decimal(row.get("discount"))) + self._decimal(row.get("tax"))
        row["total"] = self._money(total)

    def _recalculate_row(self, row_index: int) -> None:
        if 0 <= row_index < len(self.lines):
            self.lines[row_index]["qty"] = self._clamp_qty_for_row(row_index, self._decimal(self.lines[row_index].get("qty")))
            self._recalculate_row_data(self.lines[row_index])

    def _has_column(self, key: str) -> bool:
        return any(col.key == key for col in self.columns)

    def total_amount(self) -> Decimal:
        return sum((self._decimal(row.get("total")) for row in self.lines if row.get("item_id")), Decimal("0"))

    def discount_amount(self) -> Decimal:
        return sum((self._decimal(row.get("discount")) for row in self.lines if row.get("item_id")), Decimal("0"))

    def tax_amount(self) -> Decimal:
        return sum((self._decimal(row.get("tax")) for row in self.lines if row.get("item_id")), Decimal("0"))

    def subtotal_amount(self) -> Decimal:
        total = Decimal("0")
        for row in self.lines:
            if not row.get("item_id"):
                continue
            price = self._decimal(row.get("price")) or self._decimal(row.get("cost"))
            if self._has_column("cost") and not self._has_column("price"):
                price = self._decimal(row.get("cost"))
            total += self._decimal(row.get("qty")) * price
        return self._money(total)

    def get_lines_data(self) -> list[dict[str, Any]]:
        payload = []
        for row in self.lines:
            if not row.get("item_id"):
                continue
            qty = self._decimal(row.get("qty"))
            if qty <= 0:
                continue
            unit_price = self._decimal(row.get("price")) or self._decimal(row.get("cost"))
            if self._has_column("cost") and not self._has_column("price"):
                unit_price = self._decimal(row.get("cost"))
            conversion_factor = self._positive_decimal(row.get("conversion_factor") or 1)
            base_qty = qty * conversion_factor
            payload.append({
                "item_id": row.get("item_id"),
                "item_name": row.get("item", ""),
                "barcode": row.get("barcode", ""),
                "quantity": qty,
                "unit": row.get("unit", ""),
                "unit_id": row.get("unit_id"),
                "unit_price": unit_price,
                "unit_cost": unit_price,
                "total": self._decimal(row.get("total")),
                "description": row.get("notes", ""),
                "conversion_factor": conversion_factor,
                "variant_id": row.get("variant_id"),
                "variant_color": row.get("variant_color", ""),
                "variant_size": row.get("variant_size", ""),
                "variant_sku": row.get("variant_sku", ""),
                "barcode_scope": row.get("barcode_scope", ""),
                "matched_barcode": row.get("matched_barcode") or row.get("barcode", ""),
                "base_qty": base_qty,
                "quantity_in_base": base_qty,
                "discount_percent": 0,
                "tax_percent": 0,
                "batch": row.get("batch", ""),
                "expiry": row.get("expiry", ""),
            })
        return payload

    def get_return_lines_data(self) -> list[dict[str, Any]]:
        payload = []
        for row in self.lines:
            if not row.get("item_id") or not row.get("original_invoice_line_id"):
                continue
            qty = self._decimal(row.get("qty"))
            if qty <= 0:
                continue
            conversion_factor = self._positive_decimal(row.get("conversion_factor") or 1)
            base_qty = qty * conversion_factor
            payload.append({
                "original_invoice_line_id": row.get("original_invoice_line_id"),
                "item_id": row.get("item_id"),
                "quantity": str(qty),
                "quantity_in_base": str(base_qty),
                "base_qty": str(base_qty),
                "conversion_factor": str(conversion_factor),
                "unit": row.get("unit", ""),
                "unit_id": row.get("unit_id"),
                "unit_price": str(self._decimal(row.get("price") or row.get("cost"))),
                "total": str(self._decimal(row.get("total"))),
                "reason": row.get("reason") or "",
                "notes": row.get("notes") or row.get("reason") or "",
                "restock": row.get("restock") or "",
                "variant_id": row.get("variant_id"),
                "variant_color": row.get("variant_color", ""),
                "variant_size": row.get("variant_size", ""),
                "variant_sku": row.get("variant_sku", ""),
                "barcode_scope": row.get("barcode_scope", ""),
                "matched_barcode": row.get("matched_barcode") or row.get("barcode", ""),
            })
        return payload
