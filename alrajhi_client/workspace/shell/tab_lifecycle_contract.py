# -*- coding: utf-8 -*-
"""Tab lifecycle and fixed-dashboard contract (Phase 346).

PyQt-free release contract for the shell rule requested by the operator:
Dashboard is a fixed surface, not a closable tab; closing any workspace tab must
land on another tab or on the fixed dashboard; Save commands inside tabs are routed through the shell; in the current policy a
successful save closes the owning tab without leaving a blank workspace pane.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class TabLifecycleCheck:
    key: str
    category: str
    title: str
    ok: bool
    detail: str = ""

    def as_row(self) -> dict[str, object]:
        return {
            "key": self.key,
            "category": self.category,
            "title": self.title,
            "status": "pass" if self.ok else "fail",
            "detail": self.detail,
        }


def _text(path: str, root: Path | None = None) -> str:
    base = root or ROOT
    return (base / path).read_text(encoding="utf-8")


def _method_body(source: str, def_name: str) -> str:
    marker = f"    def {def_name}"
    start = source.find(marker)
    if start < 0:
        return ""
    next_def = source.find("\n    def ", start + len(marker))
    return source[start:] if next_def < 0 else source[start:next_def]


def _check(key: str, category: str, title: str, ok: bool, detail: str = "") -> TabLifecycleCheck:
    return TabLifecycleCheck(key, category, title, bool(ok), detail)


def tab_lifecycle_checks(root: Path | None = None) -> List[TabLifecycleCheck]:
    base = root or ROOT
    main = _text("alrajhi_client/views/main_window.py", base)
    workspace = _text("alrajhi_client/shell/tab_workspace.py", base)
    dialog_tab = _text("alrajhi_client/features/dialog_documents/dialog_document_tab.py", base)
    returns = _text("alrajhi_client/features/returns/return_editor_tabs.py", base)
    return_actions = _text("alrajhi_client/features/returns/components/return_actions.py", base)

    switch_page = _method_body(main, "switch_page")
    show_dashboard = _method_body(main, "_show_fixed_dashboard")
    open_doc = _method_body(main, "_open_document_tab")
    save_current = _method_body(main, "save_current_tab")
    dialog_save = _method_body(dialog_tab, "workspace_save")
    return_workspace_save = _method_body(returns, "workspace_save")
    return_accept = _method_body(returns, "accept")

    return [
        _check(
            "dashboard_host_uses_stacked_surface",
            "dashboard",
            "Main shell hosts Dashboard through QStackedWidget instead of QTabWidget",
            "QStackedWidget" in main and "self.workspace_host" in main and "_install_fixed_dashboard_surface" in main,
        ),
        _check(
            "dashboard_fixed_surface_installed",
            "dashboard",
            "Dashboard is installed as fixedDashboardSurface with no window title",
            "fixedDashboardSurface" in main and "dashboard.setWindowTitle('')" in main,
        ),
        _check(
            "dashboard_switch_short_circuit",
            "dashboard",
            "switch_page('dashboard') routes to the fixed dashboard before opening tabs",
            "if pid == 'dashboard':" in switch_page and "_show_fixed_dashboard" in switch_page and "open_singleton" not in switch_page.split("if pid in self.pages:")[0],
        ),
        _check(
            "dashboard_no_visual_context_label",
            "dashboard",
            "Dashboard clears the action-bar context/title instead of showing a visual tab label",
            "set_context('')" in show_dashboard and "title_label.setText(translate('app_title'))" in show_dashboard,
        ),
        _check(
            "workspace_prevents_dashboard_tabs",
            "tabs",
            "TabbedWorkspace refuses fixed-surface tab ids such as dashboard",
            "FIXED_SURFACE_TAB_IDS" in workspace and '"dashboard"' in workspace and "return -1" in workspace,
        ),
        _check(
            "tab_close_has_empty_fallback_signal",
            "tabs",
            "Closing the last tab emits emptyWorkspace for dashboard fallback",
            "emptyWorkspace" in workspace and "self.emptyWorkspace.emit()" in workspace,
        ),
        _check(
            "tab_close_selects_neighbour",
            "tabs",
            "Closing a non-last tab selects previous/next valid tab",
            "next_index" in workspace and "self.setCurrentIndex(min(next_index, self.count() - 1))" in workspace,
        ),
        _check(
            "main_window_binds_empty_workspace_fallback",
            "tabs",
            "MainWindow binds emptyWorkspace to the fixed dashboard fallback",
            "emptyWorkspace.connect" in main and "_show_fixed_dashboard" in main,
        ),
        _check(
            "document_open_activates_tabbed_workspace",
            "tabs",
            "Opening any document activates the tabbed workspace host",
            "_activate_tabbed_workspace()" in open_doc and "open_tab" in open_doc,
        ),
        _check(
            "singleton_open_activates_tabbed_workspace",
            "tabs",
            "Opening non-dashboard singleton pages activates the tabbed workspace host",
            "_activate_tabbed_workspace()" in switch_page and "open_singleton" in switch_page,
        ),
        _check(
            "save_current_closure_owned_by_saved_signal",
            "save",
            "Global Save invokes save; successful closure is owned by saved-signal policy",
            "_invoke_current_tab_command" in save_current and "removeTab" not in save_current and "close_tab_at" not in save_current,
        ),
        _check(
            "dialog_document_save_excludes_direct_accept",
            "save",
            "Embedded dialog document save avoids direct accept; shell closes after saved signal",
            "'accept'" not in dialog_save and "save_without_closing" in dialog_save,
        ),
        _check(
            "return_workspace_save_uses_saved_signal_close",
            "save",
            "Return document tab save emits saved; shell closes the tab after success",
            "_save_return_document(close_after_save=False)" in return_workspace_save and "accept" not in return_workspace_save.replace("False", ""),
        ),
        _check(
            "return_accept_is_explicit_close_path",
            "save",
            "Return dialog close path is explicit and separate from workspace save",
            "_save_return_document(close_after_save=True)" in return_accept,
        ),
        _check(
            "return_action_save_uses_saved_signal_close",
            "save",
            "Return action save button persists through document path; shell close follows saved signal",
            "_save_return_document(close_after_save=False)" in return_actions,
        ),
        _check(
            "legacy_parent_tab_close_uses_lifecycle",
            "tabs",
            "Legacy document close buttons call close_tab_at when available",
            "close_tab_at(idx)" in _text("alrajhi_client/features/inventory/documents/warehouse_document_tab.py", base)
            and "close_tab_at(idx)" in _text("alrajhi_client/features/finance/documents/cashbox_document_tab.py", base)
            and "close_tab_at(idx)" in _text("alrajhi_client/features/finance/documents/bank_account_document_tab.py", base),
        ),
    ]


def tab_lifecycle_issues(root: Path | None = None) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for row in tab_lifecycle_checks(root):
        if not row.ok:
            issues.setdefault(row.category, []).append(f"{row.key}: {row.detail or row.title}")
    return issues


def tab_lifecycle_summary(root: Path | None = None) -> dict[str, object]:
    rows = tab_lifecycle_checks(root)
    issues = tab_lifecycle_issues(root)
    categories: Dict[str, int] = {}
    for row in rows:
        categories[row.category] = categories.get(row.category, 0) + 1
    return {
        "phase": 346,
        "checks": len(rows),
        "categories": categories,
        "issues": sum(len(v) for v in issues.values()),
        "issue_groups": len(issues),
        "ready": not issues,
    }


__all__: Sequence[str] = (
    "TabLifecycleCheck",
    "tab_lifecycle_checks",
    "tab_lifecycle_issues",
    "tab_lifecycle_summary",
)
