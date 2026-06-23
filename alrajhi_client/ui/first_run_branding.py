# -*- coding: utf-8 -*-
"""Phase 353 runtime helpers for branded splash/login/activation screens."""
from __future__ import annotations

from typing import Iterable, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget

from brand_assets import logo_png
from i18n import translate
from theme.brand import BRAND
from theme_manager import ThemeManager
from ui.design_system import DesignSystem


FIRST_RUN_RUNTIME_PHASE = 358  # supersedes legacy marker: FIRST_RUN_RUNTIME_PHASE = 353


def apply_first_run_surface(widget: QWidget, surface: str):
    """Apply a stable first-run surface identity for QSS and audits."""
    try:
        widget.setProperty("firstRunSurface", surface)
        widget.setProperty("brandPhase", FIRST_RUN_RUNTIME_PHASE)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    except Exception:
        pass
    return widget


def brand_logo_label(size_key: str = "brand_logo_login_px", image_size: int = 256) -> QLabel:
    label = QLabel()
    label.setObjectName("brandMark")
    label.setAlignment(Qt.AlignCenter)
    logo_px = int(BRAND.get(size_key, 96))
    label.setPixmap(QPixmap(logo_png(image_size)).scaled(logo_px, logo_px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    label.setMinimumSize(logo_px + 18, logo_px + 18)
    return label


def first_run_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("firstRunHeroTitle")
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    return label


def first_run_subtitle(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("firstRunSubtitle")
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    return label


def first_run_chip(text: str, tone: str = "info") -> QLabel:
    label = QLabel(text)
    label.setObjectName("firstRunChip")
    label.setProperty("tone", tone)
    label.setAlignment(Qt.AlignCenter)
    return label


def brand_side_panel(title: str, subtitle: str, chips: Sequence[str] | None = None, logo_size_key: str = "brand_logo_login_px") -> QFrame:
    panel = QFrame()
    panel.setObjectName("firstRunBrandPanel")
    panel.setMinimumWidth(int(BRAND.get("first_run_panel_width", 330)))
    panel.setProperty("visualRole", "firstRunBrandPanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(30, 34, 30, 34)
    layout.setSpacing(14)
    layout.setAlignment(Qt.AlignCenter)
    layout.addStretch(1)
    layout.addWidget(brand_logo_label(logo_size_key), alignment=Qt.AlignCenter)
    layout.addWidget(first_run_title(title))
    layout.addWidget(first_run_subtitle(subtitle))
    if chips:
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        chip_row.setAlignment(Qt.AlignCenter)
        for chip_text in chips:
            chip_row.addWidget(first_run_chip(chip_text))
        layout.addLayout(chip_row)
    layout.addStretch(1)
    footer = QLabel("AlRajhi ERP • Secure Desktop")
    footer.setObjectName("firstRunFooter")
    footer.setAlignment(Qt.AlignCenter)
    layout.addWidget(footer)
    return panel



def login_brand_header(title: str, subtitle: str, mode_text: str | None = None, logo_size_key: str = "brand_logo_login_header_px") -> QFrame:
    """Phase 358: compact stable login header.

    The login screen previously used the full side brand panel, which could
    overlap with translated fields and long account-switch labels on smaller
    screens.  This header keeps branding visible while reserving most of the
    dialog width for the credentials form.
    """
    panel = QFrame()
    panel.setObjectName("firstRunLoginHeader")
    panel.setProperty("visualRole", "firstRunLoginHeader")
    layout = QHBoxLayout(panel)
    layout.setContentsMargins(22, 18, 22, 18)
    layout.setSpacing(16)
    layout.setAlignment(Qt.AlignVCenter)

    logo = brand_logo_label(logo_size_key, image_size=192)
    logo.setObjectName("firstRunLoginLogo")
    layout.addWidget(logo, 0, Qt.AlignVCenter)

    text_box = QVBoxLayout()
    text_box.setSpacing(4)
    title_label = first_run_title(title)
    title_label.setObjectName("firstRunLoginTitle")
    title_label.setAlignment(Qt.AlignLeading | Qt.AlignVCenter)
    subtitle_label = first_run_subtitle(subtitle)
    subtitle_label.setObjectName("firstRunLoginSubtitle")
    subtitle_label.setAlignment(Qt.AlignLeading | Qt.AlignVCenter)
    text_box.addWidget(title_label)
    text_box.addWidget(subtitle_label)
    if mode_text:
        mode_label = first_run_chip(mode_text)
        mode_label.setObjectName("firstRunLoginModeChip")
        mode_label.setAlignment(Qt.AlignCenter)
        text_box.addWidget(mode_label, 0, Qt.AlignLeading)
    layout.addLayout(text_box, 1)
    return panel


def first_run_form_panel() -> QFrame:
    panel = QFrame()
    panel.setObjectName("firstRunFormPanel")
    panel.setProperty("visualRole", "firstRunFormPanel")
    return panel


def activation_device_panel(lines: Iterable[str]) -> QFrame:
    panel = QFrame()
    panel.setObjectName("activationDevicePanel")
    panel.setProperty("visualRole", "activationDevicePanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(6)
    title = QLabel(translate("phase233_ui_120"))
    title.setObjectName("activationDeviceTitle")
    layout.addWidget(title)
    for line in lines:
        label = QLabel(line)
        label.setObjectName("activationDeviceLine")
        label.setWordWrap(True)
        layout.addWidget(label)
    return panel


def set_first_run_primary(button):
    try:
        button.setObjectName("firstRunPrimary")
        button.setMinimumHeight(int(BRAND.get("first_run_primary_button_height", BRAND.get("brand_button_min_height", 42))))
    except Exception:
        pass
    return button


def set_first_run_secondary(button):
    try:
        button.setObjectName("firstRunSecondary")
        button.setMinimumHeight(int(BRAND.get("first_run_secondary_button_height", BRAND.get("brand_button_min_height", 42))))
    except Exception:
        pass
    return button


__all__ = [
    "FIRST_RUN_RUNTIME_PHASE",
    "apply_first_run_surface",
    "activation_device_panel",
    "brand_logo_label",
    "brand_side_panel",
    "first_run_chip",
    "first_run_form_panel",
    "first_run_subtitle",
    "first_run_title",
    "login_brand_header",
    "set_first_run_primary",
    "set_first_run_secondary",
]
