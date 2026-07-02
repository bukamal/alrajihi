# -*- coding: utf-8 -*-
"""Save-then-close workspace policy contract (Phase 347).

PyQt-free assertions for the operator-selected policy:
- Dashboard remains a fixed shell surface, never a closable tab.
- A successful Save from a main/sub document tab closes that tab.
- The close is performed by the workspace lifecycle manager, not by raw
  QDialog.accept()/removeTab() calls inside feature widgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class SaveCloseCheck:
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
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def _method_body(source: str, def_name: str) -> str:
    marker = f"    def {def_name}"
    start = source.find(marker)
    if start < 0:
        return ""
    next_def = source.find("\n    def ", start + len(marker))
    return source[start:] if next_def < 0 else source[start:next_def]


def _check(key: str, category: str, title: str, ok: bool, detail: str = "") -> SaveCloseCheck:
    return SaveCloseCheck(key, category, title, bool(ok), detail)


def save_close_checks(root: Path | None = None) -> List[SaveCloseCheck]:
    base = root or ROOT
    main = _text("alrajhi_client/views/main_window.py", base)
    workspace = _text("alrajhi_client/shell/tab_workspace.py", base)
    dialog_tab = _text("alrajhi_client/features/dialog_documents/dialog_document_tab.py", base)
    returns = _text("alrajhi_client/features/returns/return_editor_tabs.py", base)

    on_saved = _method_body(main, "_on_document_saved")
    should_close = _method_body(main, "_should_close_tab_after_save")
    close_saved = _method_body(main, "_close_saved_document_tab")
    open_doc = _method_body(main, "_open_document_tab")
    save_current = _method_body(main, "save_current_tab")
    switch_page = _method_body(main, "switch_page")
    show_dashboard = _method_body(main, "_show_fixed_dashboard")
    dialog_save = _method_body(dialog_tab, "workspace_save")
    return_save = _method_body(returns, "workspace_save")

    return [
        _check(
            "dashboard_still_fixed_surface",
            "dashboard",
            "Dashboard remains a fixed shell surface and is not opened as a tab",
            "_install_fixed_dashboard_surface" in main
            and "if pid == 'dashboard':" in switch_page
            and "_show_fixed_dashboard" in switch_page
            and "FIXED_SURFACE_TAB_IDS" in workspace
            and '"dashboard"' in workspace,
        ),
        _check(
            "dashboard_has_no_tab_visual_label",
            "dashboard",
            "Dashboard clears action context/title and does not expose a visual tab label",
            "set_context('')" in show_dashboard
            and "fixedDashboardSurface" in main
            and "dashboard.setWindowTitle('')" in main,
        ),
        _check(
            "document_saved_signal_bound_once",
            "save_close",
            "Document tabs bind saved to MainWindow._on_document_saved",
            "widget.saved.connect(lambda *_args: self._on_document_saved(widget))" in open_doc,
        ),
        _check(
            "save_success_queues_close",
            "save_close",
            "Successful Save queues a tab close after saved handlers finish",
            "QTimer.singleShot(0" in on_saved and "_close_saved_document_tab" in on_saved,
        ),
        _check(
            "save_close_opt_out_supported",
            "save_close",
            "Tabs may explicitly opt out with prevent_close_after_save/stay_open_after_save",
            "prevent_close_after_save" in should_close and "stay_open_after_save" in should_close,
        ),
        _check(
            "save_close_requires_real_tab",
            "save_close",
            "Only widgets currently inside TabbedWorkspace are closed after Save",
            "self.workspace.indexOf(widget) >= 0" in should_close,
        ),
        _check(
            "close_saved_uses_lifecycle_manager",
            "save_close",
            "Save-close uses close_tab_at, not raw removeTab/close/accept",
            "close_tab_at(index)" in close_saved
            and "removeTab" not in close_saved
            and ".close()" not in close_saved
            and "accept" not in close_saved,
        ),
        _check(
            "close_saved_marks_clean_before_close",
            "save_close",
            "Saved tab is marked clean before close to avoid discard prompt",
            "mark_dirty(tab_id, False)" in close_saved,
        ),
        _check(
            "global_save_does_not_directly_close",
            "save_close",
            "Ctrl+S invokes Save; closure is owned by saved-signal policy",
            "_invoke_current_tab_command" in save_current
            and "close_tab_at" not in save_current
            and "removeTab" not in save_current,
        ),
        _check(
            "embedded_dialog_save_still_safe",
            "save_close",
            "Embedded dialog save avoids direct accept; shell closes the tab after saved emits",
            "save_without_closing" in dialog_save and "'accept'" not in dialog_save,
        ),
        _check(
            "return_workspace_save_still_emits_shell_close",
            "save_close",
            "Returns save through the document save path; saved signal triggers shell close",
            "_save_return_document(close_after_save=False)" in return_save,
        ),
        _check(
            "tab_close_fallback_preserved",
            "tabs",
            "Closing the last tab still falls back to the fixed dashboard",
            "emptyWorkspace" in workspace and "self.emptyWorkspace.emit()" in workspace,
        ),
    ]


def save_close_issues(root: Path | None = None) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for row in save_close_checks(root):
        if not row.ok:
            issues.setdefault(row.category, []).append(f"{row.key}: {row.detail or row.title}")
    return issues


def save_close_summary(root: Path | None = None) -> dict[str, object]:
    rows = save_close_checks(root)
    issues = save_close_issues(root)
    categories: Dict[str, int] = {}
    for row in rows:
        categories[row.category] = categories.get(row.category, 0) + 1
    return {
        "phase": 347,
        "checks": len(rows),
        "categories": categories,
        "issues": sum(len(v) for v in issues.values()),
        "issue_groups": len(issues),
        "ready": not issues,
    }


__all__: Sequence[str] = (
    "SaveCloseCheck",
    "save_close_checks",
    "save_close_issues",
    "save_close_summary",
)
