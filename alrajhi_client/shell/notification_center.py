# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import qtawesome as qta
from PyQt5.QtCore import Qt, QDateTime, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from i18n.translator import translate, qt_layout_direction


@dataclass
class NotificationItem:
    title: str
    message: str = ""
    level: str = "info"
    source: str = "system"
    created_at: str = ""
    action_key: str = ""

    def normalized_level(self) -> str:
        level = (self.level or "info").strip().lower()
        return level if level in {"info", "success", "warning", "error"} else "info"


class NotificationCard(QFrame):
    actionRequested = pyqtSignal(str)

    ICONS = {
        "info": "fa5s.info-circle",
        "success": "fa5s.check-circle",
        "warning": "fa5s.exclamation-triangle",
        "error": "fa5s.times-circle",
    }

    def __init__(self, item: NotificationItem, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setObjectName(f"NotificationCard_{item.normalized_level()}")
        self.setFrameShape(QFrame.NoFrame)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        level = self.item.normalized_level()
        icon = QLabel(self)
        icon.setObjectName("NotificationIcon")
        icon.setPixmap(qta.icon(self.ICONS[level]).pixmap(22, 22))
        icon.setFixedWidth(28)
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        title = QLabel(self.item.title or translate("notification.untitled"), self)
        title.setObjectName("NotificationTitle")
        title.setWordWrap(True)
        text_layout.addWidget(title)
        if self.item.message:
            message = QLabel(self.item.message, self)
            message.setObjectName("NotificationMessage")
            message.setWordWrap(True)
            text_layout.addWidget(message)
        meta_text = " · ".join(part for part in [self.item.source, self.item.created_at] if part)
        if meta_text:
            meta = QLabel(meta_text, self)
            meta.setObjectName("NotificationMeta")
            text_layout.addWidget(meta)
        layout.addLayout(text_layout, 1)

        if self.item.action_key:
            button = QToolButton(self)
            button.setText(translate("open"))
            button.setIcon(qta.icon("fa5s.external-link-alt"))
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.clicked.connect(lambda: self.actionRequested.emit(self.item.action_key))
            layout.addWidget(button)


class NotificationCenter(QFrame):
    """Dock-like notification drawer for shell alerts and non-blocking feedback.

    The center is deliberately UI-only. It reads alert payloads supplied by
    MainWindow/services and emits action keys back to the shell. No data access,
    printing, or business logic is performed here.
    """

    actionRequested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("NotificationCenter")
        self.setLayoutDirection(qt_layout_direction())
        self.setVisible(False)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._items: List[NotificationItem] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.setFixedWidth(390)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame(self)
        header.setObjectName("NotificationHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 10)
        title = QLabel(translate("notification.center"), header)
        title.setObjectName("NotificationCenterTitle")
        header_layout.addWidget(title, 1)
        self.clear_btn = QToolButton(header)
        self.clear_btn.setText(translate("notification.clear"))
        self.clear_btn.setIcon(qta.icon("fa5s.broom"))
        self.clear_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(self.clear_btn)
        self.close_btn = QToolButton(header)
        self.close_btn.setIcon(qta.icon("fa5s.times"))
        self.close_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.close_btn)
        root.addWidget(header)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget(self.scroll)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(10)
        self.content_layout.addStretch(1)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet("""
            QFrame#NotificationCenter {
                background: palette(base);
                border-left: 1px solid palette(mid);
                border-right: 1px solid palette(mid);
            }
            QFrame#NotificationHeader {
                background: palette(window);
                border-bottom: 1px solid palette(mid);
            }
            QLabel#NotificationCenterTitle { font-size: 15px; font-weight: 900; }
            QFrame[id^="NotificationCard"], QFrame#NotificationCard_info,
            QFrame#NotificationCard_success, QFrame#NotificationCard_warning,
            QFrame#NotificationCard_error {
                border: 1px solid palette(mid);
                border-radius: 12px;
                background: palette(window);
            }
            QLabel#NotificationTitle { font-weight: 900; }
            QLabel#NotificationMessage { color: palette(text); }
            QLabel#NotificationMeta { color: palette(mid); font-size: 11px; }
            QToolButton { padding: 5px 8px; border-radius: 7px; }
            QToolButton:hover { background: palette(alternate-base); }
        """)

    def set_notifications(self, items: Iterable[NotificationItem]) -> None:
        self._items = list(items)
        self._render()

    def add_notification(self, title: str, message: str = "", level: str = "info", source: str = "system", action_key: str = "") -> None:
        item = NotificationItem(
            title=title,
            message=message,
            level=level,
            source=source,
            created_at=QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm"),
            action_key=action_key,
        )
        self._items.insert(0, item)
        self._items = self._items[:50]
        self._render()

    def clear(self) -> None:  # type: ignore[override]
        self._items.clear()
        self._render()

    def show_temporary(self, title: str, message: str = "", level: str = "info", timeout_ms: int = 4500) -> None:
        self.add_notification(title, message, level=level)
        self.show()
        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self.hide)

    def _render(self) -> None:
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not self._items:
            empty = QLabel(translate("notification.empty"), self.content)
            empty.setObjectName("NotificationMessage")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            self.content_layout.insertWidget(0, empty)
            self.clear_btn.setEnabled(False)
            return
        self.clear_btn.setEnabled(True)
        for item in self._items:
            card = NotificationCard(item, self.content)
            card.actionRequested.connect(self.actionRequested.emit)
            self.content_layout.insertWidget(self.content_layout.count() - 1, card)

    def count(self) -> int:
        return len(self._items)
