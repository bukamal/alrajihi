# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QComboBox, QHeaderView, QCheckBox, QTableWidget, QTableWidgetItem
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
        self._current_rows: List[Dict[str, Any]] = []
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
        self.sold_qty_label = QLabel()
        for label in (self.variant_count_label, self.color_count_label, self.size_count_label, self.quantity_label, self.low_stock_label, self.sold_qty_label):
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("apparelMetric")
            s.addWidget(label, 1)
        root.addWidget(summary)

        reports = QFrame(self)
        reports.setObjectName("apparelReportsCard")
        reports_layout = QVBoxLayout(reports)
        reports_layout.setContentsMargins(14, 12, 14, 12)
        reports_layout.setSpacing(8)
        reports_title = QLabel(translate("apparel.reports_title"))
        reports_title.setObjectName("apparelSectionTitle")
        reports_layout.addWidget(reports_title)
        report_metrics = QHBoxLayout()
        report_metrics.setSpacing(8)
        self.report_low_label = QLabel()
        self.report_best_color_label = QLabel()
        self.report_best_size_label = QLabel()
        for label in (self.report_low_label, self.report_best_color_label, self.report_best_size_label):
            label.setAlignment(Qt.AlignCenter)
            label.setObjectName("apparelMetric")
            report_metrics.addWidget(label, 1)
        reports_layout.addLayout(report_metrics)
        self.report_table = QTableWidget(self)
        self.report_table.setObjectName("apparelReportsTable")
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setMinimumHeight(118)
        reports_layout.addWidget(self.report_table)
        root.addWidget(reports)

        builder = QFrame(self)
        builder.setObjectName("apparelBulkBuilderCard")
        b = QVBoxLayout(builder)
        b.setContentsMargins(14, 12, 14, 12)
        b.setSpacing(8)
        builder_title = QLabel(translate("apparel.bulk_builder_title"))
        builder_title.setObjectName("apparelSectionTitle")
        b.addWidget(builder_title)
        builder_row = QHBoxLayout()
        builder_row.setSpacing(8)
        self.bulk_colors_edit = QLineEdit()
        self.bulk_colors_edit.setPlaceholderText(translate("apparel.bulk_colors_placeholder"))
        self.bulk_colors_edit.setText(self._settings_csv("apparel/default_color_set", "أبيض,أسود,أزرق,أحمر"))
        builder_row.addWidget(QLabel(translate("apparel_col_color")))
        builder_row.addWidget(self.bulk_colors_edit, 2)
        self.bulk_sizes_edit = QLineEdit()
        self.bulk_sizes_edit.setPlaceholderText(translate("apparel.bulk_sizes_placeholder"))
        self.bulk_sizes_edit.setText(self._settings_csv("apparel/default_size_set", "XS,S,M,L,XL,XXL"))
        builder_row.addWidget(QLabel(translate("apparel_col_size")))
        builder_row.addWidget(self.bulk_sizes_edit, 2)
        self.bulk_code_prefix_edit = QLineEdit()
        self.bulk_code_prefix_edit.setPlaceholderText(translate("apparel.bulk_code_prefix"))
        builder_row.addWidget(QLabel(translate("apparel.variant_code_prefix")))
        builder_row.addWidget(self.bulk_code_prefix_edit, 1)
        b.addLayout(builder_row)
        builder_actions = QHBoxLayout()
        builder_actions.setSpacing(8)
        self.auto_code_check = QCheckBox(translate("apparel.auto_variant_code"))
        self.auto_code_check.setChecked(True)
        self.auto_barcode_check = QCheckBox(translate("apparel.auto_barcode"))
        self.auto_barcode_check.setChecked(str(settings_service.get("apparel/barcode_required", "true")).lower() in {"1", "true", "yes", "on"})
        self.create_bulk_btn = QPushButton(translate("apparel.create_missing_variants"))
        self.create_bulk_btn.setIcon(qta.icon("fa5s.layer-group"))
        self.create_bulk_btn.clicked.connect(self.create_missing_variants)
        builder_actions.addWidget(self.auto_code_check)
        builder_actions.addWidget(self.auto_barcode_check)
        builder_actions.addStretch(1)
        builder_actions.addWidget(self.create_bulk_btn)
        b.addLayout(builder_actions)
        root.addWidget(builder)

        self.result_label = QLabel(translate("apparel.variant_lookup_hint"))
        self.result_label.setObjectName("muted")
        root.addWidget(self.result_label)

        matrix_card = QFrame(self)
        matrix_card.setObjectName("apparelMatrixCard")
        matrix_layout = QVBoxLayout(matrix_card)
        matrix_layout.setContentsMargins(14, 12, 14, 12)
        matrix_layout.setSpacing(8)
        matrix_title = QLabel(translate("apparel.matrix_title"))
        matrix_title.setObjectName("apparelSectionTitle")
        matrix_layout.addWidget(matrix_title)
        self.matrix_table = QTableWidget(self)
        self.matrix_table.setObjectName("apparelColorSizeMatrix")
        self.matrix_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.matrix_table.setAlternatingRowColors(True)
        self.matrix_table.setMinimumHeight(170)
        matrix_layout.addWidget(self.matrix_table)
        root.addWidget(matrix_card)

        self.table = SmartTableView(self)
        self.table.set_table_identity("apparel.workspace.variant_matrix")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        self.setStyleSheet("""
            QFrame#apparelHeaderCard, QFrame#apparelControlCard, QFrame#apparelSummaryCard, QFrame#apparelReportsCard, QFrame#apparelBulkBuilderCard, QFrame#apparelMatrixCard {
                border: 1px solid palette(mid);
                border-radius: 14px;
                background: palette(base);
            }
            QLabel#apparelTitle { font-size: 20px; font-weight: 900; }
            QLabel#apparelSectionTitle { font-size: 15px; font-weight: 900; }
            QTableWidget#apparelColorSizeMatrix { gridline-color: palette(mid); border: 0; }
            QLabel#apparelMetric { padding: 10px; border-radius: 10px; background: palette(alternate-base); font-weight: 800; }
            QLineEdit, QComboBox { min-height: 34px; padding: 5px 9px; }
            QPushButton { min-height: 34px; padding: 6px 12px; font-weight: 800; }
        """)

    def _display_headers(self) -> List[str]:
        return [translate(key) for key in self.HEADERS]

    def _settings_csv(self, key: str, default: str) -> str:
        try:
            value = settings_service.get(key, default)
        except Exception:
            value = default
        return str(value or default)

    def _csv_values(self, text: str) -> List[str]:
        values: List[str] = []
        seen = set()
        for part in str(text or "").replace(";", ",").split(","):
            value = part.strip()
            if not value:
                continue
            marker = value.casefold()
            if marker in seen:
                continue
            seen.add(marker)
            values.append(value)
        return values

    def _variant_code(self, item: Dict[str, Any], color: str, size: str, index: int) -> str:
        prefix = self.bulk_code_prefix_edit.text().strip() if hasattr(self, "bulk_code_prefix_edit") else ""
        if not prefix:
            prefix = str(item.get("barcode") or item.get("id") or "ITEM")
        def clean(value: str) -> str:
            return "".join(ch for ch in str(value or "").strip().upper() if ch.isalnum())[:6] or "X"
        return f"{clean(prefix)}-{clean(color)}-{clean(size)}-{index:02d}"

    def _variant_identity_set(self, rows: List[Dict[str, Any]]) -> set[Tuple[str, str]]:
        return {
            (str(row.get("color") or "").strip().casefold(), str(row.get("size") or "").strip().casefold())
            for row in rows
        }

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
        self._current_rows = rows
        model = GenericTableModel(rows, self._display_headers(), data_keys=list(self.DATA_KEYS))
        self.table.setModel(model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if hasattr(self.table, "fit_columns_to_view"):
            self.table.fit_columns_to_view()
        self._update_summary(rows)
        self._render_color_size_matrix(rows)
        self._load_apparel_reports()

    def _render_color_size_matrix(self, rows: List[Dict[str, Any]]) -> None:
        selected = self._selected_item_id
        if selected is None:
            self.matrix_table.clear()
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            return
        colors = sorted({str(row.get("color") or "—") for row in rows}, key=lambda value: value.casefold())
        sizes = sorted({str(row.get("size") or "—") for row in rows}, key=lambda value: value.casefold())
        self.matrix_table.clear()
        self.matrix_table.setRowCount(len(colors))
        self.matrix_table.setColumnCount(len(sizes))
        self.matrix_table.setVerticalHeaderLabels(colors)
        self.matrix_table.setHorizontalHeaderLabels(sizes)
        qty_by_cell: Dict[Tuple[str, str], Decimal] = {}
        for row in rows:
            key = (str(row.get("color") or "—"), str(row.get("size") or "—"))
            qty_by_cell[key] = qty_by_cell.get(key, Decimal("0")) + Decimal(str(row.get("_raw_quantity") or 0))
        for r, color in enumerate(colors):
            for c, size in enumerate(sizes):
                value = self._format_qty(qty_by_cell.get((color, size), Decimal("0")))
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.matrix_table.setItem(r, c, item)
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def create_missing_variants(self) -> None:
        item_id = self._selected_item_id
        if item_id is None:
            self.result_label.setText(translate("apparel.bulk_select_item_required"))
            return
        colors = self._csv_values(self.bulk_colors_edit.text())
        sizes = self._csv_values(self.bulk_sizes_edit.text())
        if not colors or not sizes:
            self.result_label.setText(translate("apparel.bulk_colors_sizes_required"))
            return
        try:
            result = product_service.create_missing_variants(
                int(item_id), colors, sizes,
                auto_code=self.auto_code_check.isChecked(),
                auto_barcode=self.auto_barcode_check.isChecked(),
                code_prefix=self.bulk_code_prefix_edit.text().strip() or None,
            )
        except Exception as exc:
            self.result_label.setText(str(exc))
            return
        self.result_label.setText(translate(
            "apparel.bulk_result",
            created=int(result.get("created") or 0),
            skipped=int(result.get("skipped") or 0),
            errors=int(result.get("errors") or 0),
        ))
        self._load_variants()

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

    def _load_apparel_reports(self) -> None:
        try:
            report = product_service.apparel_report(item_id=self._selected_item_id)
        except Exception:
            report = {"summary": {}, "low_stock": [], "by_color": [], "by_size": []}
        summary = report.get("summary") or {}
        self.sold_qty_label.setText(translate("apparel.metric_sold", qty=self._format_qty(summary.get("total_sold_quantity") or 0)))
        low_rows = report.get("low_stock") or []
        by_color = report.get("by_color") or []
        by_size = report.get("by_size") or []
        best_color = by_color[0] if by_color else {}
        best_size = by_size[0] if by_size else {}
        self.report_low_label.setText(translate("apparel.report_low_stock", count=len(low_rows)))
        self.report_best_color_label.setText(translate("apparel.report_top_color", color=best_color.get("color") or "—", qty=self._format_qty(best_color.get("sold_quantity") or 0)))
        self.report_best_size_label.setText(translate("apparel.report_top_size", size=best_size.get("size") or "—", qty=self._format_qty(best_size.get("sold_quantity") or 0)))
        self._render_low_stock_report(low_rows[:12])

    def _render_low_stock_report(self, rows: List[Dict[str, Any]]) -> None:
        headers = [
            translate("apparel_col_item"), translate("apparel_col_color"), translate("apparel_col_size"),
            translate("apparel_col_quantity"), translate("apparel_col_reorder_level"), translate("apparel_col_sku"),
        ]
        self.report_table.clear()
        self.report_table.setColumnCount(len(headers))
        self.report_table.setRowCount(len(rows))
        self.report_table.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            values = [
                row.get("item") or "",
                row.get("color") or "—",
                row.get("size") or "—",
                self._format_qty(row.get("quantity") or 0),
                self._format_qty(row.get("reorder_level") or 0),
                row.get("sku") or "—",
            ]
            for c, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter if c else Qt.AlignVCenter | Qt.AlignLeft)
                self.report_table.setItem(r, c, cell)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

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
