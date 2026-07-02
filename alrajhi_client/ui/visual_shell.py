# -*- coding: utf-8 -*-
"""Phase465 visual shell helpers.

These helpers are presentation-only.  They mark existing widgets with stable
visual contracts and adjust safe chrome visibility.  They must not perform data
access, persistence, routing, or business validation.
"""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtWidgets import QFrame, QPushButton, QWidget

from theme.brand import BRAND


PHASE = 465


def _set_repolished(widget: QWidget) -> None:
    try:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
    except Exception:
        pass


def apply_standard_modal_chrome(dialog: QWidget, *, role: str = "modal", allow_minimize: bool = False) -> QWidget:
    """Mark a frameless dialog as a non-overlapping standard modal.

    The visible fix is intentionally conservative: keep the inherited branded
    header and object names for older contracts, hide maximize/minimize buttons
    for true modals, and reserve a compact title bar so controls cannot overlap
    the body, especially in RTL screenshots.
    """
    try:
        dialog.setProperty("visualShellPhase", PHASE)
        dialog.setProperty("standardModalChrome", True)
        dialog.setProperty("modalChromePolicy", "single_close" if not allow_minimize else "close_minimize")
        dialog.setProperty("visualWorkspaceType", "modal")
        dialog.setProperty("dialogKind", role or "modal")
    except Exception:
        pass

    title_bar = getattr(dialog, "title_bar", None)
    if isinstance(title_bar, QFrame):
        title_bar.setProperty("visualShellPhase", PHASE)
        title_bar.setProperty("standardModalChrome", True)
        title_bar.setProperty("modalChromePolicy", "single_close" if not allow_minimize else "close_minimize")
        try:
            h = int(BRAND.get("standard_modal_titlebar_height", 44))
            title_bar.setFixedHeight(h)
        except Exception:
            pass
        _set_repolished(title_bar)

    max_btn = getattr(dialog, "max_btn", None)
    if isinstance(max_btn, QPushButton):
        max_btn.setVisible(False)
    min_btn = getattr(dialog, "min_btn", None)
    if isinstance(min_btn, QPushButton):
        min_btn.setVisible(bool(allow_minimize))
    close_btn = getattr(dialog, "close_btn", None)
    if isinstance(close_btn, QPushButton):
        close_btn.setProperty("visualShellPhase", PHASE)
        close_btn.setProperty("dialogActionRole", "close")
        try:
            close_btn.setFixedSize(int(BRAND.get("standard_modal_title_button_size", 34)), int(BRAND.get("standard_modal_title_button_size", 34)))
        except Exception:
            pass
        _set_repolished(close_btn)

    main_frame = getattr(dialog, "main_frame", None)
    if isinstance(main_frame, QFrame):
        main_frame.setProperty("visualShellPhase", PHASE)
        main_frame.setProperty("standardModalChrome", True)
        main_frame.setProperty("visualWorkspaceType", "modal")
        _set_repolished(main_frame)

    body = getattr(dialog, "content_widget", None)
    if isinstance(body, QWidget):
        body.setProperty("visualShellPhase", PHASE)
        body.setProperty("standardModalBody", True)
        _set_repolished(body)

    return dialog


def mark_visual_shell(widget: QWidget, *, surface: str, shell_type: str = "administrative") -> QWidget:
    """Attach a common visual shell contract to a page or shell widget."""
    try:
        widget.setProperty("visualShellPhase", PHASE)
        widget.setProperty("visualShellSurface", surface)
        widget.setProperty("visualShellType", shell_type)
        widget.setProperty("visualWorkspaceType", shell_type)
        _set_repolished(widget)
    except Exception:
        pass
    return widget


def set_widgets_visible(widgets: Iterable[QWidget], visible: bool) -> None:
    for widget in widgets:
        if isinstance(widget, QWidget):
            try:
                widget.setVisible(bool(visible))
            except Exception:
                pass
