from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt, QDate, QTimer, QSignalBlocker, QStringListModel
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QDateEdit,
    QSplitter,
    QTextEdit,
    QMessageBox,
    QComboBox,
    QSizePolicy,
    QShortcut,
    QToolButton,
    QWidget,
    QCompleter,
    QFrame,
)

from workspace.documents.base_document_tab import BaseDocumentTab
from workspace.documents.document_contract import descriptor_for
from core.services.catalog_service import catalog_service
from core.services.barcode_input_service import barcode_input_service
from core.services.invoice_service import invoice_service
from core.services.warehouse_service import warehouse_service
from core.services.settings_service import settings_service
from core.services.sales_return_service import sales_return_service
from core.services.purchase_return_service import purchase_return_service
from currency import currency

from .transaction_context import TransactionContext
from .i18n import tr, html_bold
from .components.transaction_bottom_actions import TransactionBottomActions
from .components.transaction_totals_panel import TransactionTotalsPanel
from .components.transaction_return_tools import TransactionReturnTools
from .components.transaction_printing_bridge import TransactionPrintingBridge
from .grids.transaction_column_presets import DEFAULT_PRESET, presets, preset_names
from .grids.transaction_column_schema import schema_for
from .grids.transaction_line_model import TransactionLineModel
from .grids.transaction_line_grid import TransactionLineGrid
from .grids.transaction_grid_preferences import TransactionGridPreferences


class TransactionDocumentTab(BaseDocumentTab):
    DOCUMENT_DESCRIPTOR = None
    """Unified ERP transaction document surface for invoices and returns.

    The tab owns the new transaction-document UI and command contract for
    save/print/export.  Legacy invoice and return dialogs remain fallback
    surfaces only; new document output is routed through the transaction
    printing bridge instead of invoice_dialog.py.
    """

    RESPONSIVE_COMPACT_WIDTH = 1040

    def __init__(self, context: TransactionContext, parent=None, invoice_id=None):
        super().__init__(context.document_type, invoice_id, parent)
        self.document_descriptor = descriptor_for(context.document_type)
        self.context = context
        self.invoice_id = invoice_id
        self.return_id = invoice_id if context.is_return else None
        self.is_return = context.is_return
        self.inv_type = context.invoice_type
        self.transaction_settings = settings_service.get_transaction_settings(context.document_type)
        self.storage_currency = currency.storage_currency()
        self.display_currency = currency.get_display_currency()
        self.columns = schema_for(context.document_type)
        self.lines_model = TransactionLineModel(self.columns, self)
        self.grid_preferences = TransactionGridPreferences()
        self.printing_bridge = TransactionPrintingBridge(self)
        self._loading = False
        self._parties_loaded = False
        self._warehouses_loaded = False
        self._return_invoices_loaded = False
        self.invoice_map: dict[object, dict] = {}
        default_preset = self.transaction_settings.get("line_grid_default_preset", DEFAULT_PRESET) or DEFAULT_PRESET
        self._manual_preset_name = self.grid_preferences.active_preset(self.context.document_type, default_preset)
        if self._manual_preset_name not in preset_names():
            self._manual_preset_name = DEFAULT_PRESET
        self._responsive_active_preset = None

        self._build_ui()
        self._install_shortcuts()
        self._load_parties()
        self._load_warehouses()
        if self.is_return:
            self._load_return_invoices()
        if self.invoice_id:
            if self.is_return:
                self.load_return_data(self.invoice_id)
            else:
                self.load_invoice_data(self.invoice_id)
        else:
            if not self.is_return:
                self.lines_model.add_empty_line()
            self._prefill_reference()
            self.set_document_title(self.workspace_title())
            self.set_dirty(False)
        self._refresh_totals()
        QTimer.singleShot(0, self._apply_responsive_grid)

    def workspace_title(self):
        if self.is_return:
            base = tr("transaction_purchase_return") if self.inv_type == "purchase" else tr("transaction_sales_return")
        else:
            base = tr("purchase_invoice") if self.inv_type == "purchase" else tr("sales_invoice")
        ref = self.ref_edit.text().strip() if hasattr(self, "ref_edit") else ""
        if self.invoice_id:
            return f"{base} {ref or self.invoice_id}"
        return self.context.title

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title_row = QHBoxLayout()
        self.title_label = QLabel(f"<b>{self.context.title}</b>")
        self.title_label.setVisible(False)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.presets_combo = QComboBox(self)
        for preset in presets():
            self.presets_combo.addItem(preset.title, preset.name)
        self._set_preset_combo(self._manual_preset_name)
        self.presets_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.auto_responsive_btn = QToolButton(self)
        self.auto_responsive_btn.setText(tr("transaction_auto_responsive"))
        self.auto_responsive_btn.setCheckable(True)
        self.auto_responsive_btn.setChecked(self.grid_preferences.auto_responsive(self.context.document_type, bool(self.transaction_settings.get("line_grid_auto_responsive", True))))
        self.auto_responsive_btn.toggled.connect(self._toggle_auto_responsive)
        save_btn = QPushButton(tr("transaction_save_shortcut"))
        self.header_save_btn = save_btn
        save_btn.clicked.connect(self.workspace_save)
        columns_btn = QPushButton(tr("transaction_columns"))
        columns_btn.clicked.connect(self._show_columns)
        reset_columns_btn = QPushButton(tr("transaction_reset_view"))
        reset_columns_btn.clicked.connect(self._reset_grid_layout)
        title_row.addStretch(1)
        title_row.addWidget(QLabel(tr("transaction_preset")))
        title_row.addWidget(self.presets_combo)
        title_row.addWidget(self.auto_responsive_btn)
        title_row.addWidget(columns_btn)
        title_row.addWidget(reset_columns_btn)
        title_row.addWidget(save_btn)
        root.addLayout(title_row)

        header = QGridLayout()
        header.setHorizontalSpacing(8)
        header.setVerticalSpacing(4)
        self.party_combo = QComboBox()
        self.party_combo.setEditable(True)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.warehouse_combo = QComboBox()
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText(tr("transaction_reference"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("transaction_search_material_barcode"))
        self.currency_label = QLabel(self._currency_label_text())
        self._install_material_completer()
        self.search_input.returnPressed.connect(self.add_item_from_search)
        add_btn = QPushButton(tr("add"))
        add_btn.clicked.connect(self.add_item_from_search)
        if self.is_return:
            self.original_invoice_combo = QComboBox()
            self.original_invoice_combo.setEditable(True)
            self.original_invoice_combo.setInsertPolicy(QComboBox.NoInsert)
            self.original_invoice_combo.setMinimumWidth(260)
            try:
                self.original_invoice_combo.completer().setCompletionMode(0)
            except Exception:
                pass
            self.original_invoice_combo.currentIndexChanged.connect(self._on_original_invoice_changed)
            self.search_input.setPlaceholderText(tr("transaction_select_original_then_load"))
            self.search_input.setEnabled(False)
            add_btn.setText(tr("transaction_load_lines"))

        fields = []
        if self.is_return:
            fields.append((tr("transaction_original_invoice"), self.original_invoice_combo))
        fields.extend([
            (tr("customers") if self.inv_type == "sale" else tr("suppliers"), self.party_combo),
            (tr("date"), self.date_edit),
            (tr("warehouses"), self.warehouse_combo),
            (tr("currency"), self.currency_label),
            (tr("transaction_reference"), self.ref_edit),
            (tr("transaction_quick_search") if not self.is_return else "", self.search_input),
            ("", add_btn),
        ])
        for col, (label, widget) in enumerate(fields):
            if label:
                header.addWidget(QLabel(label), 0, col)
            header.addWidget(widget, 1, col)
        header.setColumnStretch(0, 2)
        root.addLayout(header)

        self.return_tools = None
        if self.is_return:
            self.return_tools = TransactionReturnTools(self)
            self.return_tools.load_btn.clicked.connect(self._load_returnable_lines_for_selected_invoice)
            self.return_tools.fill_all_btn.clicked.connect(self._fill_all_return_quantities)
            self.return_tools.clear_btn.clicked.connect(self._clear_return_quantities)
            root.addWidget(self.return_tools)

        # Phase318: keep the legacy splitter object as a compatibility anchor,
        # but make the line grid the full-width primary work area. Notes and the
        # invoice summary move below the grid in a compact footer, so sales and
        # purchase invoices share the same operational structure.
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.grid = TransactionLineGrid(self.columns, self, identity=f"transaction_lines_{self.context.document_type}")
        self.grid.configure_item_delegate(
            items_provider=self._material_lookup_rows,
            price_key_provider=self._line_price_key,
            availability_provider=self._warehouse_available_for_item,
            item_transform=self._transaction_item_to_display,
        )
        self.grid.setModel(self.lines_model)
        self._restore_grid_layout()
        try:
            self.grid.horizontalHeader().sectionMoved.connect(self._save_grid_layout)
            self.grid.horizontalHeader().sectionResized.connect(self._save_grid_layout)
        except Exception:
            pass
        self.grid.setMinimumHeight(430)
        root.addWidget(self.grid, 1)

        self.side_panel = QFrame(self)
        self.side_panel.setObjectName("TransactionFooterPanel")
        side_layout = QHBoxLayout(self.side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(78)
        self.notes.setPlaceholderText(tr("transaction_notes_terms_attachments"))
        self.totals_panel = TransactionTotalsPanel(self)
        if hasattr(self.totals_panel, "set_currency"):
            self.totals_panel.set_currency(self.display_currency)
        if hasattr(self.totals_panel, "set_transaction_type"):
            self.totals_panel.set_transaction_type(self.inv_type)
        self.totals_panel.paidChanged.connect(self._payment_changed)
        self.totals_panel.pay_full_btn.clicked.connect(self._mark_paid_full)
        self.totals_panel.unpaid_btn.clicked.connect(self._mark_unpaid)
        if self.is_return:
            self.totals_panel.payment_frame.setToolTip(tr("transaction_return_payment_tooltip"))
            self.totals_panel.unpaid_btn.setText(tr("transaction_credit_settlement"))
            self.totals_panel.pay_full_btn.setText(tr("transaction_refund_full"))
        side_layout.addWidget(self.notes, 1)
        side_layout.addWidget(self.totals_panel, 2)
        root.addWidget(self.side_panel)

        actions = [
            ("transaction_new", self._new),
            ("transaction_add_line_insert", self._add_empty_line_from_ui if not self.is_return else self._load_returnable_lines_for_selected_invoice),
        ]
        if self.is_return:
            actions.extend([
                ("transaction_return_fill_all", self._fill_all_return_quantities),
                ("transaction_return_clear_qty", self._clear_return_quantities),
            ])
        actions.extend([
            ("transaction_delete_line_delete", self._remove_current_line),
            ("save", self.workspace_save),
            ("print", self.workspace_print),
            ("transaction_pay_full" if not self.is_return else "transaction_refund_full", self._mark_paid_full),
            ("transaction_hold" if not self.is_return else "transaction_credit_settlement", self._mark_unpaid),
            ("transaction_close", self.close),
        ])
        self.bottom_actions = TransactionBottomActions(actions, self)
        root.addWidget(self.bottom_actions)
        try:
            self.apply_document_permissions()
        except Exception:
            pass

        self.lines_model.dataChanged.connect(lambda *_: self._line_changed())
        self.lines_model.rowsInserted.connect(lambda *_: self._line_changed())
        self.lines_model.rowsRemoved.connect(lambda *_: self._line_changed())
        self.notes.textChanged.connect(lambda: self.set_dirty(True) if not self._loading else None)
        self.date_edit.dateChanged.connect(lambda *_: self.set_dirty(True) if not self._loading else None)
        self.ref_edit.textChanged.connect(lambda *_: self.set_dirty(True) if not self._loading else None)
        self.party_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True) if not self._loading else None)
        self.warehouse_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True) if not self._loading else None)
        self.totals_panel.payment_method_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True) if not self._loading else None)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, activated=self.workspace_save)
        QShortcut(QKeySequence.Print, self, activated=self.workspace_print)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._focus_search)
        QShortcut(QKeySequence("Insert"), self, activated=self._add_empty_line_from_ui if not self.is_return else self._load_returnable_lines_for_selected_invoice)
        QShortcut(QKeySequence("Delete"), self, activated=self._remove_current_line)

    def _focus_search(self) -> None:
        if self.is_return:
            self.original_invoice_combo.setFocus()
            return
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _return_service(self):
        return purchase_return_service if self.inv_type == "purchase" else sales_return_service

    def _load_parties(self) -> None:
        self.party_combo.clear()
        self.party_combo.addItem(tr("transaction_no_party"), None)
        try:
            rows = catalog_service.suppliers(limit=200) if self.inv_type == "purchase" else catalog_service.customers(limit=200)
        except Exception:
            rows = []
        for row in rows:
            self.party_combo.addItem(row.get("name", f"#{row.get('id')}"), row.get("id"))
        self._parties_loaded = True

    def _load_warehouses(self) -> None:
        self.warehouse_combo.clear()
        default_id = None
        try:
            default_id = self.transaction_settings.get("default_warehouse_id") or warehouse_service.default_warehouse_id()
        except Exception:
            default_id = None
        try:
            warehouses = warehouse_service.warehouses()
        except Exception:
            warehouses = []
        for warehouse in warehouses:
            self.warehouse_combo.addItem(warehouse.get("name", f"#{warehouse.get('id')}"), warehouse.get("id"))
            if default_id and str(warehouse.get("id")) == str(default_id):
                self.warehouse_combo.setCurrentIndex(self.warehouse_combo.count() - 1)
        self._warehouses_loaded = True

    def _load_return_invoices(self) -> None:
        if not self.is_return:
            return
        self.original_invoice_combo.clear()
        self.invoice_map = {}
        self.original_invoice_combo.addItem(tr("transaction_choose_original_invoice"), None)
        try:
            invoices = (
                purchase_return_service.purchase_invoices(limit=500)
                if self.inv_type == "purchase"
                else sales_return_service.sale_invoices(limit=500)
            )
        except Exception:
            invoices = []
        with QSignalBlocker(self.original_invoice_combo):
            self.original_invoice_combo.clear()
            self.original_invoice_combo.addItem(tr("transaction_choose_original_invoice"), None)
            for inv in invoices:
                party = inv.get("supplier_name") if self.inv_type == "purchase" else inv.get("customer_name")
                text = f"{inv.get('reference') or inv.get('id')} — {inv.get('date') or ''} — {party or tr('transaction_no_party')}"
                self.original_invoice_combo.addItem(text, inv.get("id"))
                self.invoice_map[inv.get("id")] = inv
        self._return_invoices_loaded = True

    def _prefill_reference(self) -> None:
        if self.ref_edit.text().strip():
            return
        try:
            if self.is_return:
                self.ref_edit.setText(self._return_service().next_return_no())
            else:
                self.ref_edit.setText(invoice_service.next_reference(self.inv_type))
        except Exception:
            pass

    def _select_combo_data(self, combo: QComboBox, value, fallback_label: str = "") -> None:
        if value in (None, ""):
            combo.setCurrentIndex(0 if combo.count() else -1)
            return
        for idx in range(combo.count()):
            if str(combo.itemData(idx)) == str(value):
                combo.setCurrentIndex(idx)
                return
        combo.addItem(fallback_label or f"#{value}", value)
        combo.setCurrentIndex(combo.count() - 1)

    def _selected_party_id(self):
        return self.party_combo.currentData()

    def _selected_warehouse_id(self):
        return self.warehouse_combo.currentData()

    def _line_price_key(self) -> str:
        return "purchase_price" if self.inv_type == "purchase" else "selling_price"

    def _variant_label(self, variant: dict | None) -> str:
        variant = variant or {}
        return " / ".join(
            str(value or "").strip()
            for value in (variant.get("color"), variant.get("size"))
            if str(value or "").strip()
        )

    def _variant_lookup_label(self, item: dict, variant: dict) -> str:
        base_name = str(item.get("name") or item.get("item_name") or "").strip()
        parts = [base_name]
        variant_text = self._variant_label(variant)
        if variant_text:
            parts.append(variant_text)
        code = str(variant.get("sku") or "").strip()
        if code:
            parts.append(code)
        barcode = str(variant.get("barcode") or "").strip()
        if barcode:
            parts.append(barcode)
        return " — ".join(part for part in parts if part)

    def _variant_row_from_item(self, item: dict, variant: dict) -> dict:
        row = dict(item or {})
        variant = dict(variant or {})
        barcode = str(variant.get("barcode") or "").strip()
        matched_variant = {
            "id": variant.get("id"),
            "variant_id": variant.get("id"),
            "color": variant.get("color") or "",
            "size": variant.get("size") or "",
            "sku": variant.get("sku") or "",
            "barcode": barcode,
            "sale_price": variant.get("sale_price"),
            "cost_price": variant.get("cost_price"),
            "quantity": variant.get("quantity") or "0",
            "reorder_level": variant.get("reorder_level") or "0",
        }
        row.update({
            "base_item_name": item.get("name") or item.get("item_name") or "",
            "variant_id": variant.get("id"),
            "variant_color": variant.get("color") or "",
            "variant_size": variant.get("size") or "",
            "variant_sku": variant.get("sku") or "",
            "variant": self._variant_label(variant),
            "matched_variant": matched_variant,
            "barcode_scope": "variant",
            "matched_barcode": barcode,
            # A variant row must never fall back to the base-material barcode in
            # transaction grids.  Empty variant barcode remains empty so the
            # cashier/accountant does not accidentally post to the base material.
            "barcode": barcode,
            "lookup_label": self._variant_lookup_label(item, variant),
            "search_label": self._variant_lookup_label(item, variant),
        })
        def first_price(*values):
            for value in values:
                if value not in (None, ""):
                    return value
            return None
        sale_price = first_price(
            variant.get("sale_price"),
            item.get("selling_price"),
            item.get("sale_price"),
            item.get("retail_price"),
        )
        cost_price = first_price(
            variant.get("cost_price"),
            item.get("purchase_price"),
            item.get("average_cost"),
            item.get("cost_price"),
        )
        if sale_price not in (None, ""):
            row["selling_price"] = sale_price
            if self.inv_type == "sale":
                row["price"] = sale_price
                row["unit_price"] = sale_price
        if cost_price not in (None, ""):
            row["purchase_price"] = cost_price
            row["average_cost"] = cost_price
            if self.inv_type == "purchase":
                row["price"] = cost_price
                row["unit_price"] = cost_price
        return row

    def _material_lookup_rows(self, search: str | None = None, limit: int = 60) -> list[dict]:
        rows = catalog_service.items(search=search or None, limit=limit) or []
        normalized_search = str(search or "").strip().casefold()
        if normalized_search and not rows:
            # A user may type only a color, size, variant code, or variant barcode.
            # Base material search will not find that text, so perform a bounded
            # catalog pass and filter the expanded variant labels below.
            try:
                rows = catalog_service.items(search=None, limit=max(limit or 60, 200)) or []
            except Exception:
                rows = []
        expanded: list[dict] = []
        for row in rows:
            item = dict(row or {})
            variants = []
            try:
                item_id = int(item.get("id") or 0)
                variants = catalog_service.item_variants(item_id) if item_id else []
            except Exception:
                variants = []
            if variants:
                for variant in variants:
                    variant_row = self._variant_row_from_item(item, variant)
                    label = str(variant_row.get("lookup_label") or "").casefold()
                    barcode = str(variant_row.get("matched_barcode") or "").casefold()
                    # Keep all variants when the user searched by the base material
                    # name; filter only when the typed text clearly targets a
                    # specific variant/code/barcode.
                    if (
                        not normalized_search
                        or normalized_search in str(item.get("name") or item.get("item_name") or "").casefold()
                        or normalized_search in label
                        or normalized_search in barcode
                    ):
                        expanded.append(self._item_prices_to_display(variant_row))
                # For apparel items, transactions should normally select a
                # concrete color/size variant.  The base row is intentionally
                # not offered in manual suggestions to avoid selling/purchasing
                # the general material by mistake.  Scanning the base barcode is
                # still supported for ordinary/non-variant workflows.
                continue
            expanded.append(self._item_prices_to_display(item))
        return expanded[:limit] if limit else expanded

    def _item_has_active_variants(self, item: dict | None) -> bool:
        item = item or {}
        if item.get("variant_id") or item.get("matched_variant"):
            return False
        try:
            item_id = int(item.get("id") or 0)
        except Exception:
            item_id = 0
        if not item_id:
            return False
        cache = getattr(self, "_apparel_base_variant_cache", None)
        if cache is None:
            cache = {}
            self._apparel_base_variant_cache = cache
        if item_id not in cache:
            try:
                cache[item_id] = bool(catalog_service.item_variants(item_id))
            except Exception:
                cache[item_id] = False
        return bool(cache[item_id])

    def _transaction_item_to_display(self, item: dict | None) -> dict | None:
        """Normalize a resolved transaction item while blocking apparel bases.

        Material documents may show the parent material, but invoices must post
        concrete color/size variants.  This transform is used by quick search
        and the editable item-cell delegate in both local and API modes.
        """
        if not item:
            return None
        if self._item_has_active_variants(item):
            return None
        return self._item_prices_to_display(item)

    def _warehouse_available_for_item(self, item: dict):
        if self.inv_type != "sale" or not item or not item.get("id"):
            return None
        variant_id = item.get("variant_id") or (item.get("matched_variant") or {}).get("variant_id") or (item.get("matched_variant") or {}).get("id")
        return warehouse_service.available_qty(int(item.get("id")), self._selected_warehouse_id(), variant_id=variant_id)

    def _selected_original_invoice_id(self):
        return self.original_invoice_combo.currentData() if self.is_return and hasattr(self, "original_invoice_combo") else None

    def _on_original_invoice_changed(self) -> None:
        if self._loading or not self.is_return:
            return
        inv = self.invoice_map.get(self._selected_original_invoice_id()) or {}
        party_id = inv.get("supplier_id") if self.inv_type == "purchase" else inv.get("customer_id")
        party_name = inv.get("supplier_name") if self.inv_type == "purchase" else inv.get("customer_name")
        self._select_combo_data(self.party_combo, party_id, party_name or "")
        if inv.get("warehouse_id"):
            self._select_combo_data(self.warehouse_combo, inv.get("warehouse_id"), inv.get("warehouse_name") or "")
        self._load_returnable_lines_for_selected_invoice()
        self.set_dirty(True)

    def _install_material_completer(self) -> None:
        """Install case-insensitive material/barcode suggestions for the quick line field."""
        self._material_completer_model = QStringListModel(self)
        self._material_completer = QCompleter(self._material_completer_model, self.search_input)
        self._material_completer.setCaseSensitivity(Qt.CaseInsensitive)
        try:
            self._material_completer.setFilterMode(Qt.MatchContains)
        except Exception:
            pass
        self._material_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_input.setCompleter(self._material_completer)
        self._material_completer_timer = QTimer(self)
        self._material_completer_timer.setSingleShot(True)
        self._material_completer_timer.timeout.connect(self._refresh_material_completer)
        self.search_input.textEdited.connect(lambda _text: self._material_completer_timer.start(160))

    def _refresh_material_completer(self) -> None:
        if self.is_return or not hasattr(self, "_material_completer_model"):
            return
        text = self.search_input.text().strip()
        try:
            normalized = barcode_input_service.normalize(text)
            if normalized and barcode_input_service.looks_like_scan(normalized):
                self._material_completer_model.setStringList([])
                return
            rows = self._material_lookup_rows(text or None, 50) or []
        except Exception:
            rows = []
        self._material_completer_rows = rows
        seen = set()
        terms = []
        for row in rows:
            values = [
                row.get("lookup_label"),
                row.get("search_label"),
                row.get("name"),
                row.get("item_name"),
                row.get("barcode"),
                row.get("code"),
                row.get("matched_barcode"),
            ]
            for value in values:
                value = str(value or "").strip()
                key = value.casefold()
                if value and key not in seen:
                    seen.add(key)
                    terms.append(value)
        self._material_completer_model.setStringList(terms)

    def _load_returnable_lines_for_selected_invoice(self) -> None:
        if not self.is_return:
            return
        invoice_id = self._selected_original_invoice_id()
        if not invoice_id:
            return
        try:
            lines = self._return_service().invoice_returnable_lines(invoice_id)
        except Exception as exc:
            QMessageBox.warning(self, tr("sales_returns") if self.inv_type == "sale" else tr("purchase_returns"), str(exc))
            lines = []
        label = self.original_invoice_combo.currentText()
        self.lines_model.load_returnable_lines(self._invoice_lines_to_display(lines), original_invoice_label=label, return_kind=self.inv_type)
        self._refresh_totals()
        if getattr(self, "return_tools", None):
            if lines:
                self.return_tools.set_message(tr("transaction_loaded_returnable_lines", count=len(lines)))
                self._refresh_return_tools_summary()
            else:
                self.return_tools.set_message(tr("transaction_no_returnable_lines"))

    def add_item_from_search(self) -> None:
        if self.is_return:
            self._load_returnable_lines_for_selected_invoice()
            return
        text = self.search_input.text().strip()
        if not text:
            return
        item = self._row_for_search_text(text)
        lookup = None
        if not item:
            try:
                lookup = barcode_input_service.lookup_entry(text, mode="auto")
                item = lookup.item
            except Exception as exc:
                QMessageBox.warning(self, tr("items"), str(exc))
                return
        if not item:
            message_key = getattr(lookup, "message_key", "transaction_item_not_found") if lookup is not None else "transaction_item_not_found"
            QMessageBox.warning(self, tr("items"), tr(message_key))
            return
        item = self._transaction_item_to_display(item)
        if not item:
            QMessageBox.warning(self, tr("items"), tr("apparel.transaction_base_item_blocked"))
            return
        available = None
        try:
            if self.inv_type == "sale" and item.get("id"):
                variant_id = item.get("variant_id") or (item.get("matched_variant") or {}).get("variant_id") or (item.get("matched_variant") or {}).get("id")
                available = warehouse_service.available_qty(int(item.get("id")), self._selected_warehouse_id(), variant_id=variant_id)
        except Exception:
            available = None
        self.lines_model.add_item(item, self._line_price_key(), warehouse_available=available)
        self.search_input.clear()
        self.set_dirty(True)
        self._refresh_totals()
        self.grid.scrollToBottom()

    def _row_for_search_text(self, text: str) -> dict | None:
        needle = str(text or "").strip().casefold()
        if not needle:
            return None
        rows = getattr(self, "_material_completer_rows", None) or []
        if not rows:
            try:
                rows = self._material_lookup_rows(text, 80)
            except Exception:
                rows = []
        for row in rows or []:
            candidates = (
                row.get("lookup_label"),
                row.get("search_label"),
                row.get("matched_barcode"),
                row.get("barcode"),
                row.get("code"),
                row.get("variant"),
            )
            if any(str(value or "").strip().casefold() == needle for value in candidates):
                return dict(row)
        return None

    def _add_empty_line_from_ui(self) -> None:
        if self.is_return:
            self._load_returnable_lines_for_selected_invoice()
            return
        self.lines_model.add_empty_line()
        self.set_dirty(True)

    def _remove_current_line(self) -> None:
        row = None
        if hasattr(self.grid, "current_source_row"):
            row = self.grid.current_source_row()
        if row is None:
            row = self.grid.currentIndex().row()
        self.lines_model.remove_line(row)
        self.set_dirty(True)
        self._refresh_totals()

    def _new(self) -> None:
        self._loading = True
        try:
            self.invoice_id = None
            self.return_id = None
            self.document_state.document_id = None
            self.lines_model.clear(keep_empty=not self.is_return)
            self.notes.clear()
            self.ref_edit.clear()
            self.totals_panel.set_paid(0.0)
            self.totals_panel.set_payment_method(self.transaction_settings.get("default_payment_method", "cash"))
            self.date_edit.setDate(QDate.currentDate())
            if self.is_return and hasattr(self, "original_invoice_combo"):
                self.original_invoice_combo.setCurrentIndex(0 if self.original_invoice_combo.count() else -1)
            self._prefill_reference()
        finally:
            self._loading = False
        self.set_document_title(self.workspace_title())
        self.title_label.setText(f"<b>{self.workspace_title()}</b>")
        self.set_dirty(False)
        self._refresh_totals()

    def _line_changed(self) -> None:
        self._refresh_totals()
        if not self._loading:
            self.set_dirty(True)

    def _payment_changed(self) -> None:
        self._refresh_totals()
        if not self._loading:
            self.set_dirty(True)

    def _decimal(self, value) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except Exception:
            return Decimal("0")

    def _currency_label_text(self) -> str:
        try:
            symbol = currency.get_currency_symbol(self.display_currency)
            return f"{self.display_currency} {symbol}".strip()
        except Exception:
            return str(getattr(self, "display_currency", currency.display_currency()) or currency.display_currency())

    def _to_display_money(self, value) -> Decimal:
        try:
            return Decimal(str(currency.convert(value or 0, self.storage_currency, self.display_currency)))
        except Exception:
            return self._decimal(value)

    def _to_storage_money(self, value) -> Decimal:
        try:
            return Decimal(str(currency.convert(value or 0, self.display_currency, self.storage_currency)))
        except Exception:
            return self._decimal(value)

    def _exchange_rate_to_usd(self) -> float:
        try:
            return float(currency.get_current_rate(self.display_currency))
        except Exception:
            return 1.0

    def _item_prices_to_display(self, item: dict | None) -> dict:
        item = dict(item or {})
        for key in ("purchase_price", "selling_price", "price", "unit_price", "base_unit_price", "average_cost"):
            if item.get(key) not in (None, ""):
                item[key] = self._to_display_money(item.get(key))
        matched = item.get("matched_unit")
        if isinstance(matched, dict):
            matched = dict(matched)
            for key in ("purchase_price", "selling_price", "price", "unit_price", "base_unit_price"):
                if matched.get(key) not in (None, ""):
                    matched[key] = self._to_display_money(matched.get(key))
            item["matched_unit"] = matched
        matched_variant = item.get("matched_variant")
        if isinstance(matched_variant, dict):
            matched_variant = dict(matched_variant)
            for key in ("sale_price", "cost_price", "price", "unit_price"):
                if matched_variant.get(key) not in (None, ""):
                    matched_variant[key] = self._to_display_money(matched_variant.get(key))
            item["matched_variant"] = matched_variant
        return item

    def _invoice_lines_to_display(self, lines: list[dict] | None) -> list[dict]:
        converted = []
        for line in lines or []:
            row = dict(line or {})
            for key in ("unit_price", "price", "unit_cost", "cost", "total", "discount", "tax", "unit_price_usd"):
                if row.get(key) not in (None, ""):
                    row[key] = self._to_display_money(row.get(key))
            converted.append(row)
        return converted

    def _invoice_lines_to_storage(self, lines: list[dict]) -> list[dict]:
        converted = []
        for line in lines or []:
            row = dict(line or {})
            for key in ("unit_price", "unit_cost", "total"):
                if row.get(key) not in (None, ""):
                    row[key] = self._to_storage_money(row.get(key))
            converted.append(row)
        return converted

    def _return_lines_to_storage(self, lines: list[dict]) -> list[dict]:
        converted = []
        for line in lines or []:
            row = dict(line or {})
            for key in ("unit_price", "total"):
                if row.get(key) not in (None, ""):
                    row[key] = str(self._to_storage_money(row.get(key)))
            converted.append(row)
        return converted

    def _refresh_totals(self) -> None:
        subtotal = self.lines_model.subtotal_amount()
        discount = self.lines_model.discount_amount()
        tax = self.lines_model.tax_amount()
        net_total = self.lines_model.total_amount()
        paid = self.totals_panel.paid_amount() if hasattr(self, "totals_panel") else Decimal("0")
        remaining = net_total - paid
        if hasattr(self, "totals_panel"):
            self.totals_panel.set_totals(subtotal, discount, tax, paid, remaining, net_total)
        self._refresh_return_tools_summary()

    def _refresh_return_tools_summary(self) -> None:
        if not self.is_return or not getattr(self, "return_tools", None):
            return
        try:
            summary = self.lines_model.return_summary()
            self.return_tools.set_summary(
                summary.get("selected_qty"),
                summary.get("returnable_qty"),
                summary.get("selected_total"),
            )
        except Exception:
            self.return_tools.set_message(tr("transaction_return_summary_failed"))

    def _fill_all_return_quantities(self) -> None:
        if not self.is_return:
            return
        changed = self.lines_model.fill_return_quantities_to_max()
        self._refresh_totals()
        if changed:
            self.set_dirty(True)
        elif getattr(self, "return_tools", None):
            self.return_tools.set_message(tr("transaction_no_returnable_quantities"))

    def _clear_return_quantities(self) -> None:
        if not self.is_return:
            return
        changed = self.lines_model.clear_return_quantities()
        self._refresh_totals()
        if changed:
            self.set_dirty(True)

    def _mark_paid_full(self) -> None:
        self.totals_panel.mark_paid_full(self.lines_model.total_amount())

    def _mark_unpaid(self) -> None:
        self.totals_panel.mark_unpaid()

    def _show_columns(self) -> None:
        if hasattr(self.grid, "show_column_chooser"):
            self.grid.show_column_chooser()
        self.grid_preferences.save_visible_keys(self.grid, self.context.document_type)
        self._save_grid_layout()

    def _set_preset_combo(self, preset_name: str) -> None:
        if not hasattr(self, "presets_combo"):
            return
        with QSignalBlocker(self.presets_combo):
            for index in range(self.presets_combo.count()):
                if str(self.presets_combo.itemData(index)) == str(preset_name):
                    self.presets_combo.setCurrentIndex(index)
                    return

    def _on_preset_changed(self) -> None:
        preset_name = self.presets_combo.currentData() or DEFAULT_PRESET
        self._manual_preset_name = str(preset_name)
        self._apply_named_grid_preset(self._manual_preset_name, persist=True)
        self._apply_responsive_grid()

    def _apply_named_grid_preset(self, preset_name: str, persist: bool = False) -> None:
        self.grid.apply_named_preset(preset_name)
        self._responsive_active_preset = preset_name
        if persist:
            self.grid_preferences.save_active_preset(self.context.document_type, preset_name)
            self.grid_preferences.save_visible_keys(self.grid, self.context.document_type)
            self._save_grid_layout()

    def _restore_grid_layout(self) -> None:
        self.grid.apply_named_preset(self._manual_preset_name)
        self.grid_preferences.restore_visible_keys(self.grid, self.context.document_type)
        self.grid_preferences.restore_header_state(self.grid, self.context.document_type)
        self.grid.fit_transaction_columns()

    def _save_grid_layout(self, *_args) -> None:
        try:
            self.grid_preferences.save_header_state(self.grid, self.context.document_type)
        except Exception:
            pass

    def _reset_grid_layout(self) -> None:
        self.grid_preferences.reset_document_layout(self.context.document_type)
        self._manual_preset_name = DEFAULT_PRESET
        self._set_preset_combo(DEFAULT_PRESET)
        self.grid.apply_named_preset(DEFAULT_PRESET)
        self.grid.fit_transaction_columns()
        self.grid_preferences.save_active_preset(self.context.document_type, DEFAULT_PRESET)
        self.grid_preferences.save_visible_keys(self.grid, self.context.document_type)
        self._save_grid_layout()

    def _toggle_auto_responsive(self, enabled: bool) -> None:
        self.grid_preferences.save_auto_responsive(self.context.document_type, enabled)
        self._apply_responsive_grid()

    def _apply_responsive_grid(self) -> None:
        if not hasattr(self, "grid") or not hasattr(self, "auto_responsive_btn"):
            return
        if not self.auto_responsive_btn.isChecked():
            return
        target = "compact" if self.width() and self.width() < self.RESPONSIVE_COMPACT_WIDTH else self._manual_preset_name
        if target == self._responsive_active_preset:
            return
        self.grid.apply_named_preset(target)
        self._responsive_active_preset = target

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        QTimer.singleShot(0, self._apply_responsive_grid)

    def load_invoice_data(self, invoice_id) -> None:
        self._loading = True
        try:
            invoice = invoice_service.get(invoice_id)
            if not invoice:
                QMessageBox.warning(self, tr("sales_invoice") if not self.is_return else tr("sales_returns"), tr("transaction_invoice_not_found"))
                return
            loaded_type = invoice.get("type")
            if loaded_type in ("sale", "purchase"):
                self.inv_type = loaded_type
            party_id = invoice.get("supplier_id") if self.inv_type == "purchase" else invoice.get("customer_id")
            fallback_party = invoice.get("supplier_name") if self.inv_type == "purchase" else invoice.get("customer_name")
            self._select_combo_data(self.party_combo, party_id, fallback_party or "")
            date_text = invoice.get("date") or QDate.currentDate().toString("yyyy-MM-dd")
            parsed = QDate.fromString(str(date_text)[:10], "yyyy-MM-dd")
            self.date_edit.setDate(parsed if parsed.isValid() else QDate.currentDate())
            self.ref_edit.setText(str(invoice.get("reference") or ""))
            self.notes.setPlainText(str(invoice.get("notes") or ""))
            self._select_combo_data(self.warehouse_combo, invoice.get("warehouse_id"), invoice.get("warehouse_name") or "")
            paid = self._to_display_money(invoice.get("paid_amount", invoice.get("paid", 0)))
            self.totals_panel.set_paid(paid)
            self.totals_panel.set_payment_method(invoice.get("payment_method") or invoice.get("payment_type") or invoice.get("payment") or "cash")
            self.lines_model.load_invoice_lines(self._invoice_lines_to_display(invoice.get("lines") or []))
            self.invoice_id = invoice_id
            self.document_state.document_id = invoice_id
            self.title_label.setText(f"<b>{self.workspace_title()}</b>")
            self.set_document_title(self.workspace_title())
            self._refresh_totals()
        except Exception as exc:
            QMessageBox.warning(self, tr("sales_invoice") if not self.is_return else tr("sales_returns"), str(exc))
        finally:
            self._loading = False
            self.set_dirty(False)

    def load_return_data(self, return_id) -> None:
        self._loading = True
        try:
            ret = self._return_service().get(return_id)
            if not ret:
                QMessageBox.warning(self, tr("sales_returns") if self.inv_type == "sale" else tr("purchase_returns"), tr("transaction_return_not_found"))
                return
            original_invoice_id = ret.get("original_invoice_id")
            self._select_combo_data(
                self.original_invoice_combo,
                original_invoice_id,
                ret.get("invoice_reference") or str(original_invoice_id or ""),
            )
            party_id = ret.get("supplier_id") if self.inv_type == "purchase" else ret.get("customer_id")
            party_name = ret.get("supplier_name") if self.inv_type == "purchase" else ret.get("customer_name")
            self._select_combo_data(self.party_combo, party_id, party_name or "")
            date_text = ret.get("date") or QDate.currentDate().toString("yyyy-MM-dd")
            parsed = QDate.fromString(str(date_text)[:10], "yyyy-MM-dd")
            self.date_edit.setDate(parsed if parsed.isValid() else QDate.currentDate())
            self.ref_edit.setText(str(ret.get("return_no") or ""))
            self.notes.setPlainText(str(ret.get("notes") or ""))
            self._select_combo_data(self.warehouse_combo, ret.get("warehouse_id"), ret.get("warehouse_name") or "")
            self.totals_panel.set_paid(self._to_display_money(ret.get("refund_amount", 0)))
            self.totals_panel.set_payment_method(self._ui_payment_method(ret.get("payment_method") or "credit_only"))
            self.lines_model.load_return_lines(self._invoice_lines_to_display(ret.get("lines") or []), ret)
            self.invoice_id = return_id
            self.return_id = return_id
            self.document_state.document_id = return_id
            self.title_label.setText(f"<b>{self.workspace_title()}</b>")
            self.set_document_title(self.workspace_title())
            self._refresh_totals()
        except Exception as exc:
            QMessageBox.warning(self, tr("sales_returns") if self.inv_type == "sale" else tr("purchase_returns"), str(exc))
        finally:
            self._loading = False
            self.set_dirty(False)

    def _ui_payment_method(self, method: str | None) -> str:
        if method in ("credit_only", "credit"):
            return "credit"
        if method in ("bank", "bank_transfer"):
            return "bank_transfer"
        if method in ("card",):
            return "card"
        return "cash"

    def _service_return_payment_method(self) -> str:
        method = self.totals_panel.payment_method()
        refund = self.totals_panel.paid_amount()
        if refund <= 0 or method == "credit":
            return "credit_only"
        if method == "bank_transfer":
            return "bank"
        return "cash" if method in {"cash", "card"} else method

    def _payload(self) -> dict:
        if self.is_return:
            return self._return_payload()
        party_id = self._selected_party_id()
        paid_display = self.totals_panel.paid_amount()
        total_display = self.lines_model.total_amount()
        paid = self._to_storage_money(paid_display)
        total = self._to_storage_money(total_display)
        return {
            "type": self.inv_type,
            "customer_id": party_id if self.inv_type == "sale" else None,
            "supplier_id": party_id if self.inv_type == "purchase" else None,
            "warehouse_id": self._selected_warehouse_id(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "reference": self.ref_edit.text().strip() or invoice_service.next_reference(self.inv_type),
            "notes": self.notes.toPlainText().strip(),
            "total": total,
            "paid_amount": paid,
            "paid": paid,
            "remaining": total - paid,
            "payment_method": self.totals_panel.payment_method(),
            "payment_status": "paid" if paid >= total and total > 0 else ("partial" if paid > 0 else "unpaid"),
            "lines": self._invoice_lines_to_storage(self.lines_model.get_lines_data()),
            "exchange_rate_to_usd": self._exchange_rate_to_usd(),
            "original_currency": self.display_currency,
        }

    def _return_payload(self) -> dict:
        total_display = self.lines_model.total_amount()
        refund_display = self.totals_panel.paid_amount()
        method = self._service_return_payment_method()
        if method == "credit_only":
            refund_display = Decimal("0")
        total = self._to_storage_money(total_display)
        refund = self._to_storage_money(refund_display)
        return {
            "return_no": self.ref_edit.text().strip(),
            "original_invoice_id": self._selected_original_invoice_id(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "warehouse_id": self._selected_warehouse_id(),
            "refund_amount": str(refund),
            "payment_method": method,
            "notes": self.notes.toPlainText().strip(),
            "total": str(total),
            "lines": self._return_lines_to_storage(self.lines_model.get_return_lines_data()),
            "exchange_rate_to_usd": self._exchange_rate_to_usd(),
            "original_currency": self.display_currency,
        }


    def _message_title(self) -> str:
        if self.is_return:
            return tr("sales_returns") if self.inv_type == "sale" else tr("purchase_returns")
        return tr("purchase_invoice") if self.inv_type == "purchase" else tr("sales_invoice")

    def _validate_before_save(self, lines: list[dict]) -> bool:
        title = self._message_title()
        if self.is_return and self._selected_original_invoice_id() in (None, ""):
            QMessageBox.warning(self, title, tr("transaction_select_original_before_save"))
            return False
        if not lines:
            QMessageBox.warning(self, title, tr("transaction_add_at_least_one_line"))
            return False
        if self._selected_warehouse_id() in (None, ""):
            QMessageBox.warning(self, title, tr("transaction_select_warehouse_before_save"))
            return False
        if self.totals_panel.paid_amount() > self.lines_model.total_amount():
            QMessageBox.warning(self, title, tr("transaction_paid_exceeds_total"))
            return False
        if self.is_return:
            errors = self.lines_model.return_validation_errors()
            if errors:
                QMessageBox.warning(self, title, "\n".join(errors[:10]))
                return False
            return True
        if self._selected_party_id() in (None, ""):
            role = tr("customers") if self.inv_type == "sale" else tr("suppliers")
            reply = QMessageBox.question(
                self,
                tr("sales_invoice") if not self.is_return else tr("sales_returns"),
                tr("transaction_save_without_party", role=role),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False
        if self.inv_type == "sale":
            insufficient = []
            for row in self.lines_model.lines:
                if not row.get("item_id"):
                    continue
                available = row.get("available")
                if available in (None, ""):
                    continue
                try:
                    if self._decimal(row.get("qty")) > self._decimal(available):
                        insufficient.append(str(row.get("item") or row.get("barcode") or row.get("item_id")))
                except Exception:
                    pass
            if insufficient:
                QMessageBox.warning(self, tr("nav_inventory"), tr("transaction_qty_exceeds_available") + "\n" + "\n".join(insufficient[:8]))
                return False
        return True

    def workspace_save(self) -> None:
        lines = self.lines_model.get_return_lines_data() if self.is_return else self.lines_model.get_lines_data()
        if not self._validate_before_save(lines):
            return
        payload = self._payload()
        try:
            if self.is_return:
                service = self._return_service()
                if self.invoice_id:
                    saved_id = service.update_return(self.invoice_id, payload)
                else:
                    saved_id = service.create_return(payload)
                self.invoice_id = saved_id
                self.return_id = saved_id
                self.document_state.document_id = saved_id
                if payload.get("return_no"):
                    self.ref_edit.setText(payload.get("return_no", ""))
                QMessageBox.information(self, tr("sales_returns") if self.inv_type == "sale" else tr("purchase_returns"), tr("transaction_return_saved"))
            else:
                if self.invoice_id:
                    invoice_service.update(self.invoice_id, payload)
                    saved_id = self.invoice_id
                else:
                    saved_id = invoice_service.create(payload)
                    self.invoice_id = saved_id
                    self.document_state.document_id = saved_id
                self.ref_edit.setText(payload.get("reference", ""))
                QMessageBox.information(self, tr("sales_invoice") if not self.is_return else tr("sales_returns"), tr("transaction_invoice_saved"))
            self.set_document_title(self.workspace_title())
            self.title_label.setText(f"<b>{self.workspace_title()}</b>")
            self.set_dirty(False)
            self.saved.emit(self.invoice_id)
        except Exception as exc:
            QMessageBox.warning(self, tr("transaction_save_failed"), str(exc))

    def _has_printable_lines(self) -> bool:
        lines = self.lines_model.get_return_lines_data() if self.is_return else self.lines_model.get_lines_data()
        return bool(lines)

    def _ensure_saved_for_output(self) -> bool:
        title = self._message_title()
        if not self._has_printable_lines():
            QMessageBox.warning(self, tr("printing"), tr("transaction_no_printable_lines_output"))
            return False
        if self.is_dirty() or not self.invoice_id:
            reply = QMessageBox.question(
                self,
                tr("printing"),
                tr("transaction_save_before_output", title=title),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return False
            self.workspace_save()
            if self.is_dirty() or not self.invoice_id:
                return False
        return True

    def _preview_document(self) -> None:
        if not self._has_printable_lines():
            QMessageBox.warning(self, tr("printing"), tr("transaction_no_printable_lines_preview"))
            return
        self.workspace_print()

    def _open_html_preview(self) -> None:
        if not self._has_printable_lines():
            QMessageBox.warning(self, tr("printing"), tr("transaction_no_printable_lines_preview"))
            return
        self.workspace_print()

    def workspace_print(self) -> None:
        if not self._ensure_saved_for_output():
            return
        self.printing_bridge.print()

    def workspace_export(self) -> None:
        # Phase 235: no independent PDF button/path from transaction documents.
        self.workspace_print()

    def _save_and_print_placeholder(self) -> None:
        self.workspace_save()
        if not self.is_dirty():
            self.workspace_print()
