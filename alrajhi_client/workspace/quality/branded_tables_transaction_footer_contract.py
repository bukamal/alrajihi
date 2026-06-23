# -*- coding: utf-8 -*-
"""Phase 355 guard contract: branded tables and transaction footer.

PyQt-free validation for the visual runtime sweep that standardizes table
focus, headers, transaction totals and bottom command buttons across invoice,
purchase, return and similar editable document screens.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.table_identity import (
    REQUIRED_TABLE_OBJECT_MARKERS,
    REQUIRED_TABLE_QSS_MARKERS,
    TABLE_IDENTITY_PHASE,
    table_identity_matrix,
    validate_table_identity_tokens,
)

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_TABLE_RUNTIME_FILES = (
    "alrajhi_client/theme/table_identity.py",
    "alrajhi_client/theme/brand.py",
    "alrajhi_client/theme/qss.py",
    "alrajhi_client/views/custom_table_view.py",
    "alrajhi_client/ui/table_keyboard_policy.py",
    "alrajhi_client/features/transactions/transaction_document_tab.py",
    "alrajhi_client/features/transactions/components/transaction_totals_panel.py",
    "alrajhi_client/features/transactions/components/transaction_bottom_actions.py",
)

REQUIRED_RUNTIME_MARKERS = {
    "alrajhi_client/views/custom_table_view.py": (
        "brand_table_surface",
        "brand_table_density",
        "init_standard_table_keyboard",
    ),
    "alrajhi_client/ui/table_keyboard_policy.py": (
        "brand_entry_table",
        "current_cell_highlight",
        "standard_initial_entry_focus",
    ),
    "alrajhi_client/features/transactions/transaction_document_tab.py": (
        "TransactionFooterPanel",
        "TransactionFooterNotes",
        "transaction_footer_role",
    ),
    "alrajhi_client/features/transactions/components/transaction_totals_panel.py": (
        "TransactionHorizontalSummaryFrame",
        "TransactionHorizontalPaymentFrame",
        "TransactionSummaryCaption",
        "TransactionSummaryValue",
        "transaction_footer_role",
    ),
    "alrajhi_client/features/transactions/components/transaction_bottom_actions.py": (
        "TransactionBottomActionBar",
        "transaction_action",
        "transaction_footer_role",
        "setMinimumWidth(126)",
    ),
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def branded_tables_transaction_footer_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase advanced to branded tables and transaction footer polish",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= TABLE_IDENTITY_PHASE else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for theme in ("light", "dark"):
        issues = validate_table_identity_tokens(get_tokens(theme))
        rows.append({
            "key": f"{theme}_table_tokens",
            "category": "tokens",
            "description": f"{theme} palette includes Phase {TABLE_IDENTITY_PHASE} table/footer tokens",
            "status": "pass" if not issues else "fail",
            "detail": "; ".join(f"{k}:{','.join(v)}" for k, v in issues.items()),
        })

    for item in table_identity_matrix(get_tokens("light")):
        rows.append({
            "key": f"table_identity_{item['kind']}_{item['key']}",
            "category": str(item["kind"]),
            "description": item["description"],
            "status": "pass" if item.get("present", True) else "fail",
            "detail": item.get("marker", item["key"]),
        })

    for path in REQUIRED_TABLE_RUNTIME_FILES:
        rows.append({
            "key": f"file_{Path(path).stem}",
            "category": "file",
            "description": "Required branded table/footer runtime file exists",
            "status": "pass" if (base / path).exists() else "fail",
            "detail": path,
        })

    qss = _read("alrajhi_client/theme/qss.py", base)
    for marker in REQUIRED_TABLE_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:36]}",
            "category": "qss",
            "description": f"QSS contains {marker}",
            "status": "pass" if marker in qss else "fail",
            "detail": marker,
        })

    searchable_paths = tuple(REQUIRED_RUNTIME_MARKERS.keys()) + ("alrajhi_client/theme/qss.py",)
    for marker in REQUIRED_TABLE_OBJECT_MARKERS:
        found = any(marker.marker in _read(path, base) for path in searchable_paths)
        rows.append({
            "key": f"object_{marker.key}",
            "category": marker.category,
            "description": marker.description,
            "status": "pass" if found else "fail",
            "detail": marker.marker,
        })

    for path, markers in REQUIRED_RUNTIME_MARKERS.items():
        text = _read(path, base)
        for marker in markers:
            rows.append({
                "key": f"runtime_{Path(path).stem}_{marker[:28]}",
                "category": "runtime",
                "description": f"{path} uses {marker}",
                "status": "pass" if marker in text else "fail",
                "detail": marker,
            })

    return rows


def branded_tables_transaction_footer_summary(root: Path | None = None) -> Dict[str, object]:
    rows = branded_tables_transaction_footer_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": TABLE_IDENTITY_PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_TABLE_RUNTIME_FILES",
    "REQUIRED_RUNTIME_MARKERS",
    "branded_tables_transaction_footer_matrix",
    "branded_tables_transaction_footer_summary",
]
