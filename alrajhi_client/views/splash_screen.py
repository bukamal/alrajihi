# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget, QApplication, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QPixmap
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from brand_assets import logo_png, APP_DISPLAY_NAME_AR, APP_DESCRIPTION_AR
from i18n import translate


class ModernSplashScreen(QSplashScreen):
    """Startup splash with explicit boot-step status and error state."""

    def __init__(self):
        pixmap = QPixmap(640, 420)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QFrame(self)
        self.container.setObjectName('card')
        self.container.setGeometry(0, 0, 640, 420)
        self.container.setObjectName('startupCard')
        self.container.setStyleSheet(DesignSystem.card_style(accent=True))
        DesignSystem.apply_shadow(self.container, blur=34, y=12, alpha=95)
        layout = QVBoxLayout(self.container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(14)
        layout.setContentsMargins(46, 38, 46, 34)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setPixmap(QPixmap(logo_png(256)).scaled(118, 118, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.logo)

        self.app_title = QLabel(APP_DISPLAY_NAME_AR)
        self.app_title.setAlignment(Qt.AlignCenter)
        self.app_title.setStyleSheet("font-size: 32px; font-weight: 900; color: white;")
        layout.addWidget(self.app_title)

        self.subtitle = QLabel(APP_DESCRIPTION_AR)
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.86);")
        layout.addWidget(self.subtitle)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        chips.setAlignment(Qt.AlignCenter)
        self.boot_chips = []
        for text in ("قاعدة البيانات", "الترخيص", "تسجيل الدخول", "الواجهة"):
            chip = QLabel(text)
            chip.setAlignment(Qt.AlignCenter)
            chip.setStyleSheet("background-color: rgba(255,255,255,0.16); color: white; border-radius: 12px; padding: 5px 10px; font-size: 11px;")
            chips.addWidget(chip)
            self.boot_chips.append(chip)
        layout.addLayout(chips)

        self.step_label = QLabel(translate('phase233_ui_002'))
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        layout.addWidget(self.step_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setFixedWidth(430)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255,255,255,0.22);
                border-radius: 6px;
                min-height: 12px;
                text-align: center;
                color: white;
                font-size: 10px;
            }
            QProgressBar::chunk { background-color: white; border-radius: 6px; }
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)

        self.status_label = QLabel(translate('phase233_ui_003'))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: rgba(255,255,255,0.78); font-size: 12px;")
        layout.addWidget(self.status_label)

        self.detail_label = QLabel(translate('phase233_ui_004'))
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: rgba(255,255,255,0.62); font-size: 11px;")
        layout.addWidget(self.detail_label)

        self.setWindowOpacity(0)
        self.show()
        self._fade_in()

    def _fade_in(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(350)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()
        self.animation = anim

    def set_progress(self, value: int, message: str = None, detail: str = None):
        value = max(0, min(100, int(value)))
        self.progress.setValue(value)
        if message:
            self.step_label.setText(message)
            self.status_label.setText(message)
        if detail:
            self.detail_label.setText(detail)
        try:
            active = 0 if value < 30 else 1 if value < 60 else 2 if value < 90 else 3
            for i, chip in enumerate(getattr(self, 'boot_chips', [])):
                if i <= active:
                    chip.setStyleSheet("background-color: white; color: #4f46e5; border-radius: 12px; padding: 5px 10px; font-size: 11px; font-weight: bold;")
                else:
                    chip.setStyleSheet("background-color: rgba(255,255,255,0.16); color: white; border-radius: 12px; padding: 5px 10px; font-size: 11px;")
        except Exception:
            pass
        QApplication.processEvents()

    def set_error(self, message: str, detail: str = None):
        self.progress.setStyleSheet("""
            QProgressBar { border: none; background-color: rgba(255,255,255,0.22); border-radius: 6px; min-height: 12px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #ef4444; border-radius: 6px; }
        """)
        self.progress.setValue(max(self.progress.value(), 5))
        self.step_label.setText(translate('phase233_ui_005'))
        self.status_label.setText(message)
        self.detail_label.setText(detail or "راجع الرسالة ثم أعد المحاولة.")
        QApplication.processEvents()

    def finish(self, main_window):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(250)
        anim.setStartValue(1)
        anim.setEndValue(0)

        def _finish_splash():
            # Do not use zero-argument super() inside a lambda/closure here;
            # PyQt calls this later without the method frame needed by super().
            QSplashScreen.finish(self, main_window)

        anim.finished.connect(_finish_splash)
        anim.start()
        self.animation = anim
