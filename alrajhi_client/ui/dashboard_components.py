# -*- coding: utf-8 -*-
"""Reusable dashboard UI components for the tabbed workspace shell.

The dashboard should not hand-roll every card and chart.  These components are
visual only: no database, no service, no printing logic.  They keep the modern
workspace look consistent while preserving the project's Service/Gateway and
unified printing boundaries.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Mapping, Sequence

import qtawesome as qta
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

try:  # pyqtgraph is declared in requirements.txt; keep a safe fallback for CI.
    import pyqtgraph as pg
except Exception:  # pragma: no cover - depends on optional GUI environment
    pg = None

from i18n import qt_layout_direction
from ui.design_system import DesignSystem


class ModernKpiCard(QFrame):
    """Compact KPI card used by dashboards and future analytics tabs."""

    def __init__(self, title: str, icon_name: str, tone: str = "primary", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ModernKpiCard")
        self.setLayoutDirection(qt_layout_direction())
        self._tone = tone
        self._accent = self._tone_color(tone)
        self.setMinimumHeight(118)
        self.setStyleSheet(self._style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setObjectName("ModernKpiIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(38, 38)
        self.icon_label.setPixmap(qta.icon(f"fa5s.{icon_name}", color="white").pixmap(QSize(18, 18)))
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ModernKpiTitle")
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.title_label.setWordWrap(True)
        header.addWidget(self.icon_label)
        header.addWidget(self.title_label, 1)
        layout.addLayout(header)

        self.value_label = QLabel("—")
        self.value_label.setObjectName("ModernKpiValue")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.value_label)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("ModernKpiHint")
        self.hint_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.hint_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(str(value))

    def set_hint(self, hint: str) -> None:
        self.hint_label.setText(str(hint or ""))

    @staticmethod
    def _tone_color(tone: str) -> str:
        colors = {
            "primary": DesignSystem.color("primary", "#2563eb"),
            "success": DesignSystem.color("success", "#059669"),
            "warning": DesignSystem.color("warning", "#f59e0b"),
            "danger": DesignSystem.color("danger", "#dc2626"),
            "info": DesignSystem.color("info", "#0ea5e9"),
        }
        return colors.get(tone, colors["primary"])

    def _style(self) -> str:
        return f"""
            QFrame#ModernKpiCard {{
                background: {DesignSystem.color('card_bg', '#ffffff')};
                border: 1px solid {DesignSystem.color('border', '#e2e8f0')};
                border-radius: 18px;
            }}
            QFrame#ModernKpiCard:hover {{
                border: 1px solid {self._accent};
            }}
            QLabel#ModernKpiIcon {{
                background: {self._accent};
                border-radius: 14px;
            }}
            QLabel#ModernKpiTitle {{
                color: {DesignSystem.color('text_secondary', '#475569')};
                font-size: 12px;
                font-weight: 800;
            }}
            QLabel#ModernKpiValue {{
                color: {DesignSystem.color('text_primary', '#0f172a')};
                font-size: 21px;
                font-weight: 900;
            }}
            QLabel#ModernKpiHint {{
                color: {DesignSystem.color('text_muted', '#64748b')};
                font-size: 11px;
                font-weight: 700;
            }}
        """


class DashboardChartPanel(QFrame):
    """Small chart panel backed by pyqtgraph with a text fallback."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DashboardChartPanel")
        self.setLayoutDirection(qt_layout_direction())
        self.setMinimumHeight(220)
        self.setStyleSheet(f"""
            QFrame#DashboardChartPanel {{
                background: {DesignSystem.color('card_bg', '#ffffff')};
                border: 1px solid {DesignSystem.color('border', '#e2e8f0')};
                border-radius: 18px;
            }}
            QLabel#DashboardChartTitle {{
                color: {DesignSystem.color('text_primary', '#0f172a')};
                font-size: 15px;
                font-weight: 900;
            }}
            QLabel#DashboardChartFallback {{
                color: {DesignSystem.color('text_muted', '#64748b')};
                font-size: 12px;
                font-weight: 700;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        title_label = QLabel(title)
        title_label.setObjectName("DashboardChartTitle")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(title_label)

        if pg is not None:
            self.plot = pg.PlotWidget(self)
            self.plot.setBackground(None)
            self.plot.showGrid(x=True, y=True, alpha=0.18)
            self.plot.hideAxis("bottom")
            self.plot.addLegend(offset=(10, 10))
            layout.addWidget(self.plot, 1)
            self.fallback = None
        else:
            self.plot = None
            self.fallback = QLabel("—")
            self.fallback.setObjectName("DashboardChartFallback")
            self.fallback.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.fallback, 1)

    def set_trend(self, rows: Sequence[Mapping[str, object]], incoming_label: str, outgoing_label: str) -> None:
        incoming = [float(Decimal(str(row.get("incoming", 0) or 0))) for row in rows]
        outgoing = [float(Decimal(str(row.get("outgoing", 0) or 0))) for row in rows]
        if self.plot is None:
            labels = [str(row.get("label", "")) for row in rows]
            self.fallback.setText(" | ".join(labels) if labels else "—")
            return
        self.plot.clear()
        x = list(range(len(rows)))
        if not x:
            x = [0]
            incoming = [0.0]
            outgoing = [0.0]
        self.plot.plot(x, incoming, pen=pg.mkPen(DesignSystem.color("success", "#059669"), width=2), symbol="o", name=incoming_label)
        self.plot.plot(x, outgoing, pen=pg.mkPen(DesignSystem.color("danger", "#dc2626"), width=2), symbol="o", name=outgoing_label)
