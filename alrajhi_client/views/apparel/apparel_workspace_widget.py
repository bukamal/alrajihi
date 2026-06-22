# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QComboBox, QHeaderView
)
import qtawesome as qta

from i18n import translate, qt_layout_direction
from core.services.product_service import product_service
from core.services.settings_service import settings_service
from currency import currency
from models.table_models import GenericTableModel
from ui.smart_table_view import SmartTableView
from utils import show_toast


class ApparelWorkspaceWidget(QWidget):
    """Standalone apparel workspace backed by ProductService item variants.

    The UI is intentionally a shell: it searches items/variant barcodes and
    presents the color/size stock matrix without creating an independent apparel
    DAO, repository, gateway, payment, or inventory engine.
    """

    HEADERS = (
        "apparel_col_item",
        "apparel_col_color",
        "apparel_col_size",
        "apparel_col_sku",
        "apparel_col_barcode",
        "apparel_col_quantity",
        "apparel_col_reorder_level",
        "apparel_col_sale_price",
        "apparel_col_status",
    )
    DATA_KEYS = (
        "item",
        "color",
        "size",
        "sku",
        "barcode",
        "quantity",
        "reorder_level",
        "sale_price",
        "status",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("apparelWorkspace")
        self.setLayoutDirection(qt_layout_direction())
        self._items: List[Dict[str, Any]] = []
        self._selected_item_id: int | None = None
        self._init_ui()
        self.refresh()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QFrame(self)
        header.setObjectName("apparelHeaderCard")
        h = QHBoxLayout(header)
        h.setContentsMargins(18, 14, 18, 14)
        h.setSpacing(12)
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.tshirt").pixmap(36, 36))
        h.addWidget(icon, 0, Qt.AlignVCenter)
        title_box = QVBoxLayout()
        self.title = QLabel(translate("apparel.workspace_title"))
        self.title.setObjectName("apparelTitle")
        self.subtitle = QLabel(translate("apparel.workspace_subtitle"))
        self.subtitle.setObjectName("muted")
        self.subtitle.setWordWrap(True)
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        h.addLayout(title_box, 1)
        self.refresh_btn = QPushButton(translate("refresh"))
        self.refresh_btn.setIcon(qta.icon("fa5s.sync-alt"))
        self.refresh_btn.clicked.connect(self.refresh)
        h.addWidget(self.refresh_btn)
        root.addWidget(header)

        controls = QFrame(self)
        controls.setObjectName("apparelControlCard")
        c = QHBoxLayout(controls)
        c.setContentsMargins(14, 12, 14, 12)
        c.setSpacing(8)
        self.item_filter = QLineEdit()
        self.item_filter.setPlaceholderText(translate("apparel.search_item_placeholder"))
        self.item_filter.textChanged.connect(self._reload_item_combo)
        c.addWidget(QLabel(translate("item")))
        c.addWidget(self.item_filter, 1)
        self.item_combo = QComboBox()
        self.item_combo.currentIndexChanged.connect(self._on_item_changed)
        c.addWidget(self.item_combo, 2)
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText(translate("apparel.scan_variant_barcode"))
        self.barcode_edit.returnPressed.connect(self.lookup_barcode)
        c.addWidget(self.barcode_edit, 1)
        self.lookup_btn = QPushButton(translate("apparel.lookup_variant"))
        self.lookup_btn.clicked.connect(self.lookup_barcode)
        c.addWidget(self.lookup_btn)
        root.addWidget(controls)

        summary = QFrame(self)
        summary.setObjectName("apparelSummaryCard")
        s = QHBoxLayout(summary)
        s.setContentsMargins(14, 12, 14, 12)
        s.setSpacing(10)
        self.variant_count_label = QLabel()
        self.color_count_label = QLabel()
        self.size_count_label = QLabel()
        self.quantity_label = QLabel()
        self.low_stock_label = QLabel()
        for label in (self.variant_count_label, self.color_count_label, self.size_count_label, self.quantity_label, self.low_stock_label):
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("apparelMetric")
            s.addWidget(label, 1)
        root.addWidget(summary)

        self.result_label = QLabel(translate("apparel.variant_lookup_hint"))
        self.result_label.setObjectName("muted")
        root.addWidget(self.result_label)

        self.table = SmartTableView(self)
        self.table.set_table_identity("apparel.workspace.variant_matrix")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        self.setStyleSheet("""
            QFrame#apparelHeaderCard, QFrame#apparelControlCard, QFrame#apparelSummaryCard {
                border: 1px solid palette(mid);
                border-radius: 14px;
                background: palette(base);
            }
            QLabel#apparelTitle { font-size: 20px; font-weight: 900; }
            QLabel#apparelMetric { padding: 10px; border-radius: 10px; background: palette(alternate-base); font-weight: 800; }
            QLineEdit, QComboBox { min-height: 34px; padding: 5px 9px; }
            QPushButton { min-height: 34px; padding: 6px 12px; font-weight: 800; }
        """)

    def _display_headers(self) -> List[str]:
        return [translate(key) for key in self.HEADERS]

    def _format_qty(self, value: Any) -> str:
        try:
            return settings_service.format_quantity(value)
        except Exception:
            return f"{Decimal(str(value or 0)):.2f}"

    def _format_money(self, value: Any) -> str:
        if value in (None, ""):
            return "—"
        try:
            amount = currency.convert(Decimal(str(value or 0)), currency.storage_currency(), currency.get_display_currency())
            return currency.format_amount(amount)
        except Exception:
            return str(value)

    def refresh(self) -> None:
        try:
            self._items = product_service.items(search=None, limit=5000, offset=0)
        except Exception as exc:
            self._items = []
            show_toast(str(exc), "error", self)
        self._reload_item_combo()

    def _reload_item_combo(self) -> None:
        needle = self.item_filter.text().strip().lower() if hasattr(self, "item_filter") else ""
        previous = self._selected_item_id
        self.item_combo.blockSignals(True)
        self.item_combo.clear()
        self.item_combo.addItem(translate("apparel.all_variant_items"), None)
        for item in self._items:
            name = str(item.get("name") or "")
            barcode = str(item.get("barcode") or "")
            if needle and needle not in name.lower() and needle not in barcode.lower():
                continue
            self.item_combo.addItem(name, item.get("id"))
        if previous is not None:
            idx = self.item_combo.findData(previous)
            if idx >= 0:
                self.item_combo.setCurrentIndex(idx)
        self.item_combo.blockSignals(False)
        self._on_item_changed()

    def _on_item_changed(self) -> None:
        self._selected_item_id = self.item_combo.currentData()
        self._load_variants()

    def _variant_rows_for_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        item_id = int(item.get("id") or 0)
        if not item_id:
            return rows
        try:
            variants = product_service.item_variants(item_id)
        except Exception:
            variants = []
        for variant in variants:
            qty = Decimal(str(variant.get("quantity") or 0))
            reorder = Decimal(str(variant.get("reorder_level") or 0))
            status_key = "stock_low" if reorder > 0 and qty <= reorder else "stock_ok"
            severity = "low" if status_key == "stock_low" else "ok"
            rows.append({
                "item": item.get("name") or variant.get("item_name") or "",
                "color": variant.get("color") or "—",
                "size": variant.get("size") or "—",
                "sku": variant.get("sku") or "—",
                "barcode": variant.get("barcode") or "—",
                "quantity": self._format_qty(qty),
                "reorder_level": self._format_qty(reorder),
                "sale_price": self._format_money(variant.get("sale_price")),
                "status": translate(status_key),
                "_row_status": severity,
                "_raw_quantity": qty,
                "_raw_reorder": reorder,
            })
        return rows

    def _load_variants(self) -> None:
        rows: List[Dict[str, Any]] = []
        selected = self._selected_item_id
        for item in self._items:
            if selected is not None and int(item.get("id") or 0) != int(selected):
                continue
            rows.extend(self._variant_rows_for_item(item))
        model = GenericTableModel(rows, self._display_headers(), data_keys=list(self.DATA_KEYS))
        self.table.setModel(model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if hasattr(self.table, "fit_columns_to_view"):
            self.table.fit_columns_to_view()
        self._update_summary(rows)

    def _update_summary(self, rows: List[Dict[str, Any]]) -> None:
        colors = {str(row.get("color") or "") for row in rows if row.get("color") not in (None, "", "—")}
        sizes = {str(row.get("size") or "") for row in rows if row.get("size") not in (None, "", "—")}
        total_qty = sum((row.get("_raw_quantity") or Decimal("0")) for row in rows)
        low = sum(1 for row in rows if row.get("_row_status") == "low")
        self.variant_count_label.setText(translate("apparel.metric_variants", count=len(rows)))
        self.color_count_label.setText(translate("apparel.metric_colors", count=len(colors)))
        self.size_count_label.setText(translate("apparel.metric_sizes", count=len(sizes)))
        self.quantity_label.setText(translate("apparel.metric_qty", qty=self._format_qty(total_qty)))
        self.low_stock_label.setText(translate("apparel.metric_low", count=low))

    def lookup_barcode(self) -> None:
        barcode = self.barcode_edit.text().strip()
        if not barcode:
            self.result_label.setText(translate("apparel.variant_lookup_hint"))
            return
        try:
            hit = product_service.item_by_barcode(barcode)
        except Exception as exc:
            self.result_label.setText(str(exc))
            return
        if not hit or hit.get("barcode_scope") != "variant":
            self.result_label.setText(translate("apparel.variant_not_found"))
            return
        variant = hit.get("matched_variant") or hit
        item_id = int(hit.get("id") or variant.get("item_id") or 0)
        idx = self.item_combo.findData(item_id)
        if idx >= 0:
            self.item_combo.setCurrentIndex(idx)
        self.result_label.setText(translate(
            "apparel.variant_found",
            item=hit.get("name") or variant.get("item_name") or "",
            color=variant.get("color") or "—",
            size=variant.get("size") or "—",
        ))
        self._highlight_barcode(barcode)

    def _highlight_barcode(self, barcode: str) -> None:
        model = self.table.model()
        if model is None:
            return
        for row in range(model.rowCount()):
            idx = model.index(row, 4)
            if str(model.data(idx, Qt.DisplayRole) or "") == barcode:
                self.table.selectRow(row)
                self.table.scrollTo(idx)
                break

    def set_global_filter(self, text: str) -> None:
        text = text or ""
        self.item_filter.setText(text)

    def refresh_current_view(self) -> None:
        self.refresh()
