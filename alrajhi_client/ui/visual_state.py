# -*- coding: utf-8 -*-
"""Semantic visual state helpers for project-wide runtime styling.

Phase441 moves small status colors away from ad-hoc ``setStyleSheet`` calls.
Widgets receive semantic dynamic properties; the central QSS decides how each
state looks in the active theme.  This keeps business logic free of hard-coded
hex colors while preserving the existing success/warning/danger semantics.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget


_VALID_STATES = {"default", "muted", "success", "warning", "danger", "info"}
_VALID_WEIGHTS = {"normal", "strong"}
_VALID_SIZES = {"caption", "body", "value"}


def _repolish(widget: QWidget) -> None:
    try:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
    except Exception:
        pass


def set_visual_state(
    widget: QWidget | None,
    state: str = "default",
    *,
    weight: str = "normal",
    size: str = "body",
    role: str | None = None,
    clear_local_style: bool = True,
) -> None:
    """Apply a semantic visual state to ``widget``.

    ``clear_local_style`` intentionally defaults to true for migrated labels and
    status frames.  It prevents legacy inline QSS from overriding the central
    theme while keeping the operation local to callers that deliberately opt in.
    """
    if widget is None:
        return
    state = state if state in _VALID_STATES else "default"
    weight = weight if weight in _VALID_WEIGHTS else "normal"
    size = size if size in _VALID_SIZES else "body"
    try:
        if clear_local_style and widget.styleSheet():
            widget.setStyleSheet("")
        widget.setProperty("visualState", state)
        widget.setProperty("visualStateWeight", weight)
        widget.setProperty("visualStateSize", size)
        widget.setProperty("visualStyleSource", "centralized_visual_state")
        if role:
            widget.setProperty("visualRole", role)
    except Exception:
        return
    _repolish(widget)


def set_status_text(widget: QWidget | None, text: str, state: str = "default", *, strong: bool = True) -> None:
    """Set text when supported and apply a caption-like status style."""
    if widget is None:
        return
    try:
        widget.setText(text)
    except Exception:
        pass
    set_visual_state(
        widget,
        state,
        weight="strong" if strong else "normal",
        size="caption",
        role="semantic_status",
    )


__all__ = ["set_visual_state", "set_status_text"]
