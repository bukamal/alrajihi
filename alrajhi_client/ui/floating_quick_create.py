# -*- coding: utf-8 -*-
"""Floating quick-create placement helpers.

Phase467 moves quick creation out of page layouts.  Existing quick-create panels
are still normal widgets for compatibility, but when opened they are reparented
to the active window and positioned as a popover/drawer overlay.  This keeps
invoice grids, POS scan bars and document headers stable while preserving the
same registry, permission, translation and service/gateway save path.
"""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget

from i18n import qt_layout_direction
from ui.inline_quick_create_registry import definition_for

FLOATING_QUICK_CREATE_HOST_MARKER = "FloatingQuickCreateHost"
# Phase468 compatibility marker: floatingSurfacePhase", "468"
# Phase469 compatibility marker: floatingSurfacePhase", "469"


def _surface_tokens() -> dict:
    """Return solid visual tokens for floating quick-create surfaces."""
    try:
        from theme_manager import ThemeManager
        colors = ThemeManager.colors()
    except Exception:
        colors = {}
    return {
        "bg": colors.get("surface_raised") or colors.get("card_bg") or colors.get("bg_panel") or "#FFFFFF",
        "border": colors.get("primary") or colors.get("border") or "#0E7AA8",
        "text": colors.get("text_primary") or "#0F172A",
        "muted": colors.get("text_secondary") or "#64748B",
        "input_bg": colors.get("input_bg") or colors.get("bg_panel") or "#FFFFFF",
        "danger": colors.get("danger") or "#D92D20",
        "primary": colors.get("primary") or "#0E7AA8",
        "primary_text": colors.get("primary_text") or colors.get("button_primary_text") or "#FFFFFF",
        "soft": colors.get("brand_soft") or "#EAF6FB",
    }


def _apply_solid_surface(panel: QWidget) -> None:
    """Harden a floating panel so it never renders transparent in runtime QSS.

    Runtime screenshots showed quick-create panels blending into their host when
    reparented to the active window.  The panel therefore receives an explicit
    widget palette, WA_StyledBackground, a local solid QSS contract and a drop
    shadow.  This stays in the UI layer and does not touch service/gateway code.
    """
    tokens = _surface_tokens()
    surface = str(panel.property("quickCreateSurface") or "floating_popover")
    radius = 18 if surface == "floating_drawer" else 14
    # Phase469: set the stylesheet-driving properties before local QSS is
    # applied and force a native opaque widget background.  Runtime screenshots
    # showed transparent quick-create cards on some Windows/QSS combinations
    # when the property was set after styling or inherited from a transparent
    # operational page.
    panel.setProperty("floatingQuickCreate", "true")
    panel.setProperty("floatingSurfaceSolid", "true")
    panel.setProperty("floatingSurfacePhase", "470")
    panel.setAttribute(Qt.WA_StyledBackground, True)
    panel.setAttribute(Qt.WA_TranslucentBackground, False)
    panel.setAttribute(Qt.WA_NoSystemBackground, False)
    panel.setWindowOpacity(1.0)
    panel.setAutoFillBackground(True)
    try:
        palette = panel.palette()
        palette.setColor(QPalette.Window, QColor(tokens["bg"]))
        palette.setColor(QPalette.Base, QColor(tokens["bg"]))
        palette.setColor(QPalette.Button, QColor(tokens["input_bg"]))
        palette.setColor(QPalette.Text, QColor(tokens["text"]))
        palette.setColor(QPalette.WindowText, QColor(tokens["text"]))
        panel.setPalette(palette)
    except Exception:
        pass
    object_selector = f"QFrame#{panel.objectName()}" if panel.objectName() else "QFrame[floatingQuickCreate=\"true\"]"
    panel.setStyleSheet(f"""
        {object_selector},
        QFrame[floatingQuickCreate="true"],
        QFrame[floatingSurfaceSolid="true"] {{
            background-color: {tokens['bg']};
            color: {tokens['text']};
            border: 2px solid {tokens['border']};
            border-radius: {radius}px;
            padding: 0px;
        }}
        QFrame[floatingQuickCreate="true"] QLabel {{
            background: transparent;
            border: none;
            color: {tokens['text']};
        }}
        QFrame[floatingQuickCreate="true"] QLabel#InlineQuickCreateSubtitle {{
            color: {tokens['muted']};
        }}
        QFrame[floatingQuickCreate="true"] QLabel#InlineQuickCreateError {{
            color: {tokens['danger']};
            background: transparent;
            border: none;
        }}
        QFrame[floatingQuickCreate="true"] QLineEdit,
        QFrame[floatingQuickCreate="true"] QTextEdit,
        QFrame[floatingQuickCreate="true"] QComboBox,
        QFrame[floatingQuickCreate="true"] QDoubleSpinBox,
        QFrame[floatingQuickCreate="true"] QSpinBox {{
            background-color: {tokens['input_bg']};
            color: {tokens['text']};
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            min-height: 36px;
            padding: 6px 10px;
        }}
        QFrame[floatingQuickCreate="true"] QScrollArea#InlineQuickCreateFormScroll,
        QFrame[floatingQuickCreate="true"] QFrame#InlineQuickCreateFormHolder {{
            background-color: {tokens['bg']};
            border: none;
        }}

        QFrame[floatingQuickCreate="true"] QPushButton#InlineQuickCreateSaveButton {{
            background-color: {tokens['primary']};
            color: {tokens['primary_text']};
            border: 1px solid {tokens['primary']};
            border-radius: 10px;
            min-height: 38px;
            padding: 7px 14px;
            font-weight: 900;
        }}
        QFrame[floatingQuickCreate="true"] QPushButton#InlineQuickCreateCancelButton {{
            background-color: {tokens['soft']};
            color: {tokens['text']};
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            min-height: 38px;
            padding: 7px 14px;
            font-weight: 850;
        }}
        QFrame[floatingQuickCreate="true"] QPushButton#InlineQuickCreateCloseButton {{
            background-color: {tokens['soft']};
            color: {tokens['text']};
            border: 1px solid #CBD5E1;
            border-radius: 9px;
            min-width: 30px;
            max-width: 30px;
            min-height: 30px;
            max-height: 30px;
            padding: 0px;
            font-weight: 950;
        }}
    """)
    try:
        existing = panel.graphicsEffect()
        if existing is None or not isinstance(existing, QGraphicsDropShadowEffect):
            shadow = QGraphicsDropShadowEffect(panel)
            shadow.setBlurRadius(38)
            shadow.setOffset(0, 12)
            shadow.setColor(QColor(15, 23, 42, 88))
            panel.setGraphicsEffect(shadow)
    except Exception:
        pass
    try:
        panel.style().unpolish(panel)
        panel.style().polish(panel)
        panel.update()
    except Exception:
        pass


def floating_surface_for(entity_type: str) -> str:
    """Return the preferred floating surface for a quick-create entity."""
    mode = definition_for(entity_type).mode
    if mode == "drawer" or mode == "card":
        return "floating_drawer"
    return "floating_popover"


def floating_width_for(entity_type: str) -> int:
    surface = floating_surface_for(entity_type)
    if surface == "floating_drawer":
        return 420
    return 360


def _clamp(value: int, low: int, high: int) -> int:
    if high < low:
        return low
    return max(low, min(value, high))


def _window_for(panel: QWidget) -> QWidget:
    window = panel.window()
    if isinstance(window, QWidget):
        return window
    return panel.parentWidget() or panel


def _anchor_point(panel: QWidget, anchor: Optional[QWidget]) -> QPoint:
    if anchor is not None and isinstance(anchor, QWidget):
        try:
            window = _window_for(panel)
            return window.mapFromGlobal(anchor.mapToGlobal(QPoint(0, anchor.height() + 6)))
        except Exception:
            pass
    try:
        focus = QApplication.focusWidget()
        if focus is not None:
            window = _window_for(panel)
            return window.mapFromGlobal(focus.mapToGlobal(QPoint(0, focus.height() + 6)))
    except Exception:
        pass
    return QPoint(24, 96)


def position_floating_quick_create(panel: QWidget, anchor: Optional[QWidget] = None) -> None:
    """Place a quick-create panel as a floating overlay without changing layouts."""
    window = _window_for(panel)
    margin = 18
    surface = str(panel.property("quickCreateSurface") or floating_surface_for(panel.property("quickCreateEntity") or "category"))
    width = int(panel.property("quickCreateWidth") or floating_width_for(panel.property("quickCreateEntity") or "category"))
    width = min(width, max(280, window.width() - margin * 2))
    panel.setFixedWidth(width)

    if surface == "floating_drawer":
        # Phase470: drawers anchor below the triggering control when possible.
        # They should not cover the global toolbar or POS scan/header bands, and
        # they must keep their own scroll area instead of growing indefinitely.
        anchor_pos = _anchor_point(panel, anchor) if anchor is not None else QPoint(margin, 96)
        y = _clamp(anchor_pos.y(), margin + 48, max(margin + 48, window.height() - 280))
        height = max(260, window.height() - y - margin)
        height = min(height, 640)
        panel.setMinimumHeight(min(height, 360))
        panel.setMaximumHeight(height)
        rtl = qt_layout_direction() == Qt.RightToLeft
        x = margin if not rtl else window.width() - width - margin
    else:
        panel.adjustSize()
        size = panel.sizeHint()
        height = min(max(size.height(), 180), max(220, window.height() - margin * 2))
        panel.setMaximumHeight(height)
        anchor_pos = _anchor_point(panel, anchor)
        x = _clamp(anchor_pos.x(), margin, window.width() - width - margin)
        y = _clamp(anchor_pos.y(), margin, window.height() - height - margin)

    panel.setGeometry(x, y, width, int(panel.maximumHeight() if surface == "floating_drawer" else panel.sizeHint().height()))
    panel.raise_()


def show_floating_quick_create(panel: QWidget, anchor: Optional[QWidget] = None) -> None:
    """Show panel as an overlay child of the active window."""
    source_parent = panel.parentWidget()
    window = _window_for(panel)
    if panel.parentWidget() is not window:
        panel.setParent(window)
    panel.setWindowFlags(Qt.Widget)
    panel.setProperty("floatingQuickCreate", "true")
    panel.setProperty("floatingOverlayHost", FLOATING_QUICK_CREATE_HOST_MARKER)
    _apply_solid_surface(panel)
    if source_parent is not None:
        panel.setProperty("floatingSourceParent", source_parent.objectName() or source_parent.__class__.__name__)
    panel.show()
    position_floating_quick_create(panel, anchor)


def hide_floating_quick_create(panel: QWidget) -> None:
    panel.hide()
