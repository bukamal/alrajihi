# -*- coding: utf-8 -*-
# Phase352 compatibility markers: brandMark brand_logo_large_px splash_width
from __future__ import annotations

from PyQt5.QtWidgets import (
    QSplashScreen,
    QProgressBar,
    QLabel,
    QVBoxLayout,
    QApplication,
    QFrame,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QPixmap

from brand_assets import logo_png, APP_DISPLAY_NAME_AR, APP_DESCRIPTION_AR
from i18n import translate
from theme.brand import BRAND
from ui.design_system import DesignSystem
from ui.first_run_branding import apply_first_run_surface
from ui.visual_shell import mark_visual_shell


class ModernSplashScreen(QSplashScreen):
    """Phase434: branded pre-login startup splash.

    This surface is intentionally pre-login only.  It presents identity and real
    boot-stage feedback before LoginDialog opens; it is not the post-login main
    window transition.
    """

    STAGES = (
        (0, "startupStageDatabase", "قاعدة البيانات"),
        (30, "startupStageLicense", "الترخيص"),
        (60, "startupStageLogin", "تسجيل الدخول"),
        (90, "startupStageShell", "الواجهة"),
    )

    def __init__(self):
        pixmap = QPixmap(int(BRAND.get("startup_splash_width", BRAND.get("splash_width", 760))), int(BRAND.get("startup_splash_height", BRAND.get("splash_height", 440))))
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("BrandedPreLoginSplashWindow")
        self.setProperty("startupPhase", 434)
        self.setProperty("visualShellPhase", 465)

        width = int(BRAND.get("startup_splash_width", 760))
        height = int(BRAND.get("startup_splash_height", 440))

        self.container = QFrame(self)
        self.container.setObjectName("brandedStartupCard")
        self.container.setGeometry(0, 0, width, height)
        self.container.setProperty("basitStartupSurface", True)
        self.container.setProperty('basitDialogSurface', 'splash')
        self.container.setProperty("startupSurfacePolicy", "phase434_prelogin_branded")
        self.container.setProperty("visualShellPhase", 465)
        self.container.setProperty("startupCollisionPolicy", "text_progress_single_status")
        self.container.setProperty("legacyYellowHeader", False)
        self.container.setProperty("interactiveStageButtons", False)
        apply_first_run_surface(self.container, 'splash')
        self.container.setStyleSheet("")
        DesignSystem.apply_shadow(self.container, blur=34, y=12, alpha=95)

        root = QVBoxLayout(self.container)
        root.setAlignment(Qt.AlignCenter)
        root.setSpacing(10)
        root.setContentsMargins(46, 32, 46, 28)

        identity_panel = QFrame()
        identity_panel.setObjectName("startupIdentityPanel")
        identity_panel.setProperty("startupIdentityPanel", True)
        identity_layout = QVBoxLayout(identity_panel)
        identity_layout.setAlignment(Qt.AlignCenter)
        identity_layout.setSpacing(6)
        identity_layout.setContentsMargins(18, 12, 18, 12)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setObjectName("startupBrandMark")
        logo_px = int(BRAND.get("startup_splash_logo_px", 76))
        self.logo.setPixmap(QPixmap(logo_png(256)).scaled(logo_px, logo_px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        identity_layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        self.app_title = QLabel(APP_DISPLAY_NAME_AR)
        self.app_title.setObjectName("startupHeroTitle")
        self.app_title.setAlignment(Qt.AlignCenter)
        self.app_title.setWordWrap(True)
        identity_layout.addWidget(self.app_title)

        self.subtitle = QLabel(APP_DESCRIPTION_AR)
        self.subtitle.setObjectName("startupHeroSubtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)
        identity_layout.addWidget(self.subtitle)
        root.addWidget(identity_panel)

        stage_row = QHBoxLayout()
        stage_row.setSpacing(8)
        stage_row.setAlignment(Qt.AlignCenter)
        self.boot_chips = []
        for _, object_name, text in self.STAGES:
            chip = QLabel(text)
            chip.setObjectName(object_name)
            chip.setProperty("startupStageChip", True)
            chip.setProperty("visualShellPhase", 465)
            chip.setProperty("firstRunStageChip", True)
            chip.setProperty("state", "pending")
            chip.setAlignment(Qt.AlignCenter)
            chip.setMinimumHeight(int(BRAND.get("startup_splash_stage_height", 28)))
            stage_row.addWidget(chip)
            self.boot_chips.append(chip)
        root.addLayout(stage_row)

        self.step_label = QLabel("جاري تهيئة النظام")
        self.step_label.setObjectName("startupStepLabel")
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setWordWrap(True)
        root.addWidget(self.step_label)

        self.progress = QProgressBar()
        self.progress.setObjectName("startupProgressTrack")
        self.progress.setProperty("startupProgressTrack", True)
        self.progress.setProperty("firstRunProgressTrack", True)
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setFixedWidth(int(BRAND.get("startup_splash_progress_width", 500)))
        self.progress.setFixedHeight(int(BRAND.get("startup_splash_progress_height", 14)))
        root.addWidget(self.progress, alignment=Qt.AlignCenter)

        self.status_label = QLabel("جاري فحص ملفات التشغيل الأساسية...")
        self.status_label.setObjectName("startupStatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self.detail_label = QLabel("سيتم فتح شاشة تسجيل الدخول بعد اكتمال فحص البداية.")
        self.detail_label.setObjectName("startupDetailLabel")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setWordWrap(True)
        root.addWidget(self.detail_label)

        self.footer_label = QLabel("AlRajhi ERP • Secure Desktop")
        self.footer_label.setObjectName("startupFooterLabel")
        self.footer_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.footer_label)

        mark_visual_shell(self.container, surface="startup_splash", shell_type="startup")
        self.setWindowOpacity(0)
        self._set_stage_state(0)
        self.show()
        self._fade_in()

    def _fade_in(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()
        self.animation = anim

    def _set_stage_state(self, value: int):
        for index, (threshold, _, _) in enumerate(self.STAGES):
            chip = self.boot_chips[index]
            if value >= threshold:
                chip.setProperty("state", "active")
            else:
                chip.setProperty("state", "pending")
            chip.style().unpolish(chip)
            chip.style().polish(chip)

    def _detail_for_value(self, value: int) -> str:
        if value < 30:
            return "فحص قاعدة البيانات المحلية أو مصدر البيانات المحدد..."
        if value < 60:
            return "التحقق من حالة الترخيص وربط الجهاز..."
        if value < 90:
            return "فتح شاشة تسجيل الدخول الآمنة..."
        return "تجهيز نافذة النظام الرئيسية..."

    def set_progress(self, value: int, message: str = None, detail: str = None):
        value = max(0, min(100, int(value)))
        self.progress.setValue(value)
        if message:
            self.step_label.setText(message)
            # Phase465: avoid duplicate visible status text on the splash.
            self.status_label.setText(detail or self._detail_for_value(value))
        if detail:
            self.detail_label.setText(detail)
        else:
            self.detail_label.setText(self._detail_for_value(value))
        self._set_stage_state(value)
        QApplication.processEvents()

    def set_error(self, message: str, detail: str = None):
        self.container.setProperty("startupError", True)
        self.progress.setProperty("startupError", True)
        self.progress.style().unpolish(self.progress)
        self.progress.style().polish(self.progress)
        self.progress.setValue(max(self.progress.value(), 5))
        self.step_label.setText(translate("phase233_ui_005"))
        self.status_label.setText(message)
        self.detail_label.setText(detail or "راجع الرسالة ثم أعد المحاولة.")
        QApplication.processEvents()

    def finish(self, main_window):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(220)
        anim.setStartValue(1)
        anim.setEndValue(0)

        def _finish_splash():
            QSplashScreen.finish(self, main_window)

        anim.finished.connect(_finish_splash)
        anim.start()
        self.animation = anim
