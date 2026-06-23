# -*- coding: utf-8 -*-
"""Phase 350 PyQt-free contract for internal Close buttons.

The user reported that Close buttons inside invoice/return creation tabs only hide
the embedded widget, while the tab-bar X correctly closes the full tab and shows
the unsaved-change confirmation.  This contract prevents direct QWidget.close()
from being used as a document close action.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Phase350Check:
    code: str
    area: str
    title: str
    path: str
    ok: bool
    detail: str = ""


def _read(base: Path, path: str) -> str:
    file_path = base / path
    return file_path.read_text(encoding="utf-8") if file_path.exists() else ""


def phase350_checks(root: Path | None = None) -> List[Phase350Check]:
    base = root or ROOT
    checks: List[Phase350Check] = []

    helper = "alrajhi_client/workspace/shell/workspace_tab_close.py"
    helper_text = _read(base, helper)
    checks.extend([
        Phase350Check(
            "helper_exists",
            "lifecycle",
            "A unified helper closes the owning workspace tab rather than child widgets",
            helper,
            "close_owning_workspace_tab" in helper_text and "owning_tab_entry" in helper_text,
        ),
        Phase350Check(
            "helper_uses_close_tab_at",
            "lifecycle",
            "Internal close delegates to close_tab_at so confirmation/fallback are centralized",
            helper,
            "workspace.close_tab_at(index)" in helper_text,
        ),
        Phase350Check(
            "helper_avoids_blank_child_close_first",
            "lifecycle",
            "The fallback QWidget.close path is only used after no owning tab is found",
            helper,
            helper_text.find("workspace.close_tab_at(index)") < helper_text.rfind("close()") if "close()" in helper_text else False,
        ),
    ])

    base_doc = "alrajhi_client/workspace/documents/base_document_tab.py"
    base_doc_text = _read(base, base_doc)
    checks.extend([
        Phase350Check(
            "base_document_request_close",
            "documents",
            "BaseDocumentTab exposes request_workspace_close for all document tabs",
            base_doc,
            "def request_workspace_close" in base_doc_text and "close_owning_workspace_tab(self)" in base_doc_text,
        ),
        Phase350Check(
            "base_document_alias",
            "documents",
            "BaseDocumentTab provides close_workspace_tab compatibility alias",
            base_doc,
            "def close_workspace_tab" in base_doc_text and "return self.request_workspace_close()" in base_doc_text,
        ),
    ])

    transaction = "alrajhi_client/features/transactions/transaction_document_tab.py"
    transaction_text = _read(base, transaction)
    checks.extend([
        Phase350Check(
            "transaction_close_button_uses_workspace_lifecycle",
            "transactions",
            "Invoice/return bottom Close button calls request_workspace_close",
            transaction,
            '("transaction_close", self.request_workspace_close)' in transaction_text,
        ),
        Phase350Check(
            "transaction_close_button_not_qwidget_close",
            "transactions",
            "Transaction bottom Close button no longer connects to self.close",
            transaction,
            '("transaction_close", self.close)' not in transaction_text,
        ),
    ])

    returns = "alrajhi_client/features/returns/return_editor_tabs.py"
    returns_text = _read(base, returns)
    checks.extend([
        Phase350Check(
            "legacy_returns_request_close",
            "returns",
            "Legacy return tabs also expose request_workspace_close",
            returns,
            "def request_workspace_close" in returns_text and "close_owning_workspace_tab(self)" in returns_text,
        ),
        Phase350Check(
            "legacy_returns_accept_routes_lifecycle",
            "returns",
            "Return close-after-save uses workspace lifecycle instead of direct QDialog.accept",
            returns,
            "self.request_workspace_close()" in returns_text and "if close_after_save:" in returns_text,
        ),
    ])

    tab_ws = "alrajhi_client/shell/tab_workspace.py"
    tab_ws_text = _read(base, tab_ws)
    checks.append(Phase350Check(
        "tab_workspace_still_owns_confirmation",
        "lifecycle",
        "TabbedWorkspace remains the owner of can_close confirmation and dashboard fallback",
        tab_ws,
        "if hasattr(widget, 'can_close') and not widget.can_close()" in tab_ws_text and "emptyWorkspace.emit()" in tab_ws_text,
    ))

    phase_doc = "PHASE350_INTERNAL_CLOSE_BUTTON_TAB_LIFECYCLE.md"
    checks.append(Phase350Check(
        "phase_doc_exists",
        "release",
        "Phase 350 documentation exists",
        phase_doc,
        (base / phase_doc).exists(),
    ))

    return checks


def phase350_issues(root: Path | None = None) -> List[Phase350Check]:
    return [check for check in phase350_checks(root) if not check.ok]


__all__ = ["Phase350Check", "phase350_checks", "phase350_issues"]
