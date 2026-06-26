# -*- coding: utf-8 -*-
"""Phase 348 PyQt-free contract for text focus, grid entry, and return unification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Phase348Check:
    code: str
    area: str
    title: str
    path: str
    ok: bool
    detail: str = ""


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contains(path: str, *needles: str) -> bool:
    text = _text(path)
    return all(needle in text for needle in needles)


def phase348_checks(root: Path | None = None) -> List[Phase348Check]:
    base = root or ROOT
    def exists(path: str) -> bool:
        return (base / path).exists()
    def read(path: str) -> str:
        return (base / path).read_text(encoding="utf-8")

    checks: List[Phase348Check] = []

    keyboard = "alrajhi_client/ui/table_keyboard_policy.py"
    keyboard_text = read(keyboard) if exists(keyboard) else ""
    checks.extend([
        Phase348Check("preferred_entry_column", "keyboard", "Editable grids focus item/material column first", keyboard, "focus_entry_column" in keyboard_text and "_standard_preferred_entry_keys" in keyboard_text and "schedule_initial_entry_focus" in keyboard_text),
        Phase348Check("editor_text_select_only", "keyboard", "Enter prepares editor text by selecting existing data without clearing it", keyboard, "_standard_prepare_active_editor" in keyboard_text and "selectAll()" in keyboard_text and "editor.clear()" not in keyboard_text),
        Phase348Check("entry_column_headers", "keyboard", "Legacy Arabic/English/German material headers are recognized", keyboard, "المادة" in keyboard_text and "material" in keyboard_text and "produkt" in keyboard_text),
    ])

    utils = "alrajhi_client/utils.py"
    utils_text = read(utils) if exists(utils) else ""
    checks.extend([
        Phase348Check("click_selects_text", "text_focus", "Text inputs select all on focus and mouse click", utils, "installEventFilter" in utils_text and "MouseButtonPress" in utils_text and "MouseButtonRelease" in utils_text and "FocusIn" in utils_text),
        Phase348Check("editable_combo_text_policy", "text_focus", "Editable combo/spinbox line edits share the text policy", utils, "QComboBox" in utils_text and "QDateEdit" in utils_text and "QDoubleSpinBox" in utils_text),
    ])

    custom = "alrajhi_client/views/custom_table_view.py"
    smart = "alrajhi_client/ui/smart_table_view.py"
    editable = "alrajhi_client/ui/editable_smart_grid.py"
    checks.extend([
        Phase348Check("custom_table_initial_focus", "keyboard", "CustomTableView schedules unified entry focus", custom, exists(custom) and "schedule_initial_entry_focus" in read(custom)),
        Phase348Check("smart_table_initial_focus", "keyboard", "SmartTableView schedules unified entry focus after model binding", smart, exists(smart) and "schedule_initial_entry_focus" in read(smart)),
        Phase348Check("editable_grid_initial_focus", "keyboard", "EditableSmartGrid schedules unified entry focus after row creation", editable, exists(editable) and "schedule_initial_entry_focus" in read(editable)),
    ])

    doc = "alrajhi_client/features/transactions/transaction_document_tab.py"
    doc_text = read(doc) if exists(doc) else ""
    checks.extend([
        Phase348Check("returns_search_enabled", "returns", "Return documents keep material/barcode entry enabled", doc, "self.search_input.setEnabled(True)" in doc_text and "transaction_search_material_barcode" in doc_text),
        Phase348Check("returns_no_original_header_gate", "returns", "Original invoice selector is not the primary return header workflow", doc, "original_invoice_combo.setVisible(False)" in doc_text and "manual_return" in doc_text),
        Phase348Check("returns_insert_adds_line", "returns", "Insert/Add line in returns adds an editable row instead of loading an invoice", doc, '("transaction_add_line_insert", self._add_empty_line_from_ui)' in doc_text),
        Phase348Check("returns_manual_save_payload", "returns", "Manual returns save grid lines when no original invoice is selected", doc, "self.lines_model.get_lines_data()" in doc_text and "not bool(self._selected_original_invoice_id())" in doc_text),
    ])

    schema = "alrajhi_client/features/transactions/grids/transaction_column_schema.py"
    schema_text = read(schema) if exists(schema) else ""
    checks.extend([
        Phase348Check("sales_return_item_editable", "returns", "Sales return item column is editable like invoices", schema, 'sales_return_schema' in schema_text and 'TransactionColumn("item", "transaction_column_item", True, True, True, 260, True)' in schema_text),
        Phase348Check("purchase_return_item_editable", "returns", "Purchase return item column is editable like invoices", schema, 'purchase_return_schema' in schema_text and schema_text.count('TransactionColumn("item", "transaction_column_item", True, True, True, 260, True)') >= 3),
    ])

    model = "alrajhi_client/features/transactions/grids/transaction_line_model.py"
    model_text = read(model) if exists(model) else ""
    checks.append(Phase348Check("manual_return_validation", "returns", "Return validation allows manual rows while keeping assisted invoice limits", model, "Manual return" in model_text and "original_line_id" in model_text and "transaction_return_line_duplicate_original" in model_text))

    sales_gateway = "alrajhi_client/gateways/local/sales_return_gateway.py"
    purchase_gateway = "alrajhi_client/gateways/local/purchase_return_gateway.py"
    checks.extend([
        Phase348Check("manual_sales_return_gateway", "returns", "Local sales return gateway supports manual editable returns", sales_gateway, exists(sales_gateway) and "_create_manual_return" in read(sales_gateway) and "_ensure_manual_return_schema" in read(sales_gateway)),
        Phase348Check("manual_purchase_return_gateway", "returns", "Local purchase return gateway supports manual editable returns", purchase_gateway, exists(purchase_gateway) and "_create_manual_return" in read(purchase_gateway) and "_ensure_manual_return_schema" in read(purchase_gateway)),
    ])

    migrations = "alrajhi_client/database/migrations.py"
    checks.append(Phase348Check("manual_return_schema", "database", "Fresh databases create nullable original invoice return headers", migrations, exists(migrations) and "original_invoice_id INTEGER," in read(migrations)))

    return checks


def phase348_issues(root: Path | None = None) -> List[Phase348Check]:
    return [check for check in phase348_checks(root) if not check.ok]


__all__ = ["Phase348Check", "phase348_checks", "phase348_issues"]
