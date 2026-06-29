# -*- coding: utf-8 -*-
"""Phase435 post-login transition overlay.

A small branded feedback surface shown after LoginDialog is accepted and before
MainWindow becomes visible.  It prevents the long login-to-main wait from
looking like a freeze, while keeping the real performance issue measurable by
StartupTimelineProfiler.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from brand_assets import logo_png
from i18n.translator import translate
from theme.brand import BRAND
from theme_manager import ThemeManager


PHASE435_OVERLAY_MARKER = "phase435_post_login_transition_overlay"


class PostLoginTransitionOverlay(QWidget):
    """Frameless branded overlay for the login-to-main-window transition."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.Dialog)
        self.setObjectName("postLoginTransitionOverlay")
        self.setProperty("phase435", PHASE435_OVERLAY_MARKER)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(int(BRAND.get("post_login_overlay_width", 620)), int(BRAND.get("post_login_overlay_height", 250)))
        self.setMinimumSize(int(BRAND.get("post_login_overlay_min_width", 560)), int(BRAND.get("post_login_overlay_min_height", 220)))
        self.setStyleSheet(ThemeManager.get_stylesheet())

        shell = QFrame(self)
        shell.setObjectName("postLoginTransitionCard")
        shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(14)
        logo = QLabel()
        logo.setObjectName("postLoginTransitionLogo")
        pix = QPixmap(logo_png())
        logo_size = int(BRAND.get("post_login_overlay_logo_px", 62))
        if not pix.isNull():
            logo.setPixmap(pix.scaled(logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(logo_size, logo_size)
        header.addWidget(logo, 0, Qt.AlignVCenter)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self.title_label = QLabel(translate("post_login_loading_title"))
        self.title_label.setObjectName("postLoginTransitionTitle")
        self.detail_label = QLabel(translate("post_login_loading_detail"))
        self.detail_label.setObjectName("postLoginTransitionDetail")
        self.detail_label.setWordWrap(True)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.detail_label)
        header.addLayout(title_box, 1)
        layout.addLayout(header)

        self.status_label = QLabel(translate("post_login_step_permissions"))
        self.status_label.setObjectName("postLoginTransitionStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setObjectName("postLoginTransitionProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(10)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(int(BRAND.get("post_login_overlay_progress_height", 12)))
        layout.addWidget(self.progress)

        self.hint_label = QLabel(translate("post_login_loading_hint"))
        self.hint_label.setObjectName("postLoginTransitionHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

    def center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)

    def update_step(self, progress: int, status: str, detail: str = "") -> None:
        self.progress.setValue(max(0, min(100, int(progress))))
        self.status_label.setText(status)
        if detail:
            self.detail_label.setText(detail)
        QApplication.processEvents()

    def show_transition(self) -> None:
        self.center_on_screen()
        self.show()
        self.raise_()
        QApplication.processEvents()

    def finish_transition(self) -> None:
        self.update_step(100, translate("post_login_step_done"), translate("post_login_loading_done"))
        self.close()
