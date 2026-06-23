# -*- coding: utf-8 -*-
"""Phase 351 PyQt-free contract for function-wide close lifecycle unification.

Close buttons inside workspace business pages must not close only their inner
QWidget.  Every document-like function should delegate to the same owning tab
lifecycle used by the tab-bar X button so confirmation, neighbour selection and
fixed Dashboard fallback remain consistent across the product.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class FunctionCloseCheck:
    code: str
    area: str
    title: str
    ok: bool
    path: str = ""
    detail: str = ""


def _text(path: str, root: Path) -> str:
    try:
        return (root / path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _check(code: str, area: str, title: str, ok: bool, path: str = "", detail: str = "") -> FunctionCloseCheck:
    return FunctionCloseCheck(code, area, title, bool(ok), path, detail)


FUNCTION_CLOSE_FILES: Sequence[tuple[str, str, str]] = (
    ("transactions", "alrajhi_client/features/transactions/transaction_document_tab.py", "request_workspace_close"),
    ("returns", "alrajhi_client/features/returns/return_editor_tabs.py", "request_workspace_close"),
    ("materials", "alrajhi_client/features/items/item_editor_tab.py", "request_workspace_close"),
    ("inventory", "alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py", "request_workspace_close"),
    ("inventory", "alrajhi_client/features/inventory/documents/warehouse_document_tab.py", "request_workspace_close"),
    ("finance", "alrajhi_client/features/finance/documents/cashbox_document_tab.py", "request_workspace_close"),
    ("finance", "alrajhi_client/features/finance/documents/bank_account_document_tab.py", "request_workspace_close"),
    ("branches", "alrajhi_client/features/branches/documents/branch_document_tab.py", "request_workspace_close"),
    ("users", "alrajhi_client/features/users/documents/user_document_tab.py", "request_workspace_close"),
    ("manufacturing", "alrajhi_client/features/manufacturing/bom_document_tab.py", "request_workspace_close"),
    ("manufacturing", "alrajhi_client/features/manufacturing/production_order_document_tab.py", "request_workspace_close"),
    ("manufacturing", "alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py", "request_workspace_close"),
)


def phase351_checks(root: Path | None = None) -> List[FunctionCloseCheck]:
    base = root or Path(__file__).resolve().parents[3]
    helper = _text("alrajhi_client/workspace/shell/functional_close_policy.py", base)
    base_doc = _text("alrajhi_client/workspace/documents/base_document_tab.py", base)
    dialog_doc = _text("alrajhi_client/features/dialog_documents/dialog_document_tab.py", base)
    release = _text("alrajhi_client/workspace/quality/release_gate_contract.py", base)

    checks: List[FunctionCloseCheck] = [
        _check(
            "functional_policy_exists",
            "lifecycle",
            "Function-aware close policy module exists",
            "WORKSPACE_FUNCTION_CLOSE_TARGETS" in helper and "request_function_workspace_close" in helper,
            "alrajhi_client/workspace/shell/functional_close_policy.py",
        ),
        _check(
            "functional_policy_delegates_to_tab_lifecycle",
            "lifecycle",
            "Function close policy delegates to close_owning_workspace_tab/close_tab_at",
            "close_owning_workspace_tab(widget)" in helper,
            "alrajhi_client/workspace/shell/functional_close_policy.py",
        ),
        _check(
            "base_document_uses_function_policy",
            "documents",
            "BaseDocumentTab request_workspace_close uses function-aware policy",
            "request_function_workspace_close" in base_doc,
            "alrajhi_client/workspace/documents/base_document_tab.py",
        ),
        _check(
            "dialog_document_binds_embedded_close_controls",
            "dialog_documents",
            "Hosted legacy dialog Close/Cancel buttons are rebound to request_workspace_close",
            "def _connect_embedded_close_controls" in dialog_doc and "clicked.connect(self.request_workspace_close)" in dialog_doc,
            "alrajhi_client/features/dialog_documents/dialog_document_tab.py",
        ),
    ]

    for area, path, expected in FUNCTION_CLOSE_FILES:
        text = _text(path, base)
        checks.append(_check(
            f"{area}_{Path(path).stem}_uses_workspace_close",
            area,
            f"{path} routes internal close through request_workspace_close",
            expected in text,
            path,
        ))
        method_section = ""
        if "def _close_parent_tab" in text:
            method_section = text[text.find("def _close_parent_tab"): text.find("\n\n", text.find("def _close_parent_tab")) if text.find("\n\n", text.find("def _close_parent_tab")) != -1 else len(text)]
        elif "def request_close" in text:
            method_section = text[text.find("def request_close"): text.find("\n\n", text.find("def request_close")) if text.find("\n\n", text.find("def request_close")) != -1 else len(text)]
        checks.append(_check(
            f"{area}_{Path(path).stem}_no_raw_inner_close_in_close_handler",
            area,
            f"{path} close handler does not raw-close or remove inner widgets",
            "self.close()" not in method_section and "removeTab" not in method_section and "close_current_tab" not in method_section,
            path,
        ))

    for key in ("transactions", "returns", "materials", "inventory", "finance", "branches", "users", "manufacturing", "dialog_documents"):
        checks.append(_check(
            f"function_key_registered_{key}",
            "registry",
            f"Function close key registered: {key}",
            f'"{key}"' in helper,
            "alrajhi_client/workspace/shell/functional_close_policy.py",
        ))

    checks.append(_check(
        "phase351_release_registered",
        "release",
        "Phase 351 is registered in release gate phases",
        '(351, "function_close_lifecycle_unification")' in release,
        "alrajhi_client/workspace/quality/release_gate_contract.py",
    ))
    return checks


def phase351_issues(root: Path | None = None) -> List[FunctionCloseCheck]:
    return [check for check in phase351_checks(root) if not check.ok]


__all__ = ["FunctionCloseCheck", "FUNCTION_CLOSE_FILES", "phase351_checks", "phase351_issues"]
