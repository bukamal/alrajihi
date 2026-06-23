# -*- coding: utf-8 -*-
"""Unified workspace-tab close helper (Phase 350).

Internal Close buttons embedded in document tabs must use the same tab lifecycle
as the tab-bar X button.  Calling ``QWidget.close()`` on an embedded tab page can
hide only the child widget and leave an empty white tab/body.  This helper walks
up the parent chain, finds the owning ``TabbedWorkspace`` entry, and delegates to
``close_tab_at()`` so dirty-state confirmation, neighbour selection, and fixed
Dashboard fallback stay centralized.
"""
from __future__ import annotations

from typing import Any


def _callable_attr(obj: Any, name: str):
    value = getattr(obj, name, None)
    return value if callable(value) else None


def owning_tab_entry(widget: Any) -> tuple[Any, int] | tuple[None, int]:
    """Return ``(tab_workspace, index)`` for the tab entry containing ``widget``.

    The widget may be the tab page itself or any child inside it.  We inspect each
    parent/child pair so the function works with direct ``TabbedWorkspace`` pages
    and with future wrapper widgets.
    """
    current = widget
    while current is not None:
        parent = current.parent() if callable(getattr(current, "parent", None)) else None
        if parent is None:
            break
        index_of = _callable_attr(parent, "indexOf")
        close_tab_at = _callable_attr(parent, "close_tab_at")
        if index_of is not None and close_tab_at is not None:
            try:
                index = int(index_of(current))
            except Exception:
                index = -1
            if index >= 0:
                return parent, index
        current = parent
    return None, -1


def close_owning_workspace_tab(widget: Any) -> bool:
    """Close the owning workspace tab through the centralized lifecycle.

    Returns ``True`` when the owning tab was found and accepted by its lifecycle
    manager.  If no owning tab exists, it falls back to a normal ``close()`` call
    for true modal/standalone widgets.
    """
    workspace, index = owning_tab_entry(widget)
    if workspace is not None and index >= 0:
        try:
            return bool(workspace.close_tab_at(index))
        except Exception:
            return False

    # Secondary fallback for old containers that expose close_current_tab on a
    # parent object rather than on the tab widget itself.
    current = widget
    while current is not None:
        parent = current.parent() if callable(getattr(current, "parent", None)) else None
        if parent is None:
            break
        close_current_tab = _callable_attr(parent, "close_current_tab")
        if close_current_tab is not None:
            try:
                return bool(close_current_tab())
            except Exception:
                return False
        current = parent

    close = _callable_attr(widget, "close")
    if close is not None:
        try:
            close()
            return True
        except Exception:
            return False
    return False


__all__ = ["owning_tab_entry", "close_owning_workspace_tab"]
