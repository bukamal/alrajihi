# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSplitter, QVBoxLayout, QWidget

from i18n import translate


class DetailPlaceholder(QFrame):
    """Reusable placeholder for master-detail ERP pages.

    It deliberately contains no data access. Pages pass selected-row summaries
    into set_summary(), and document tabs remain responsible for editing.
    """

    def __init__(self, title: str = '', parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName('DetailPlaceholder')
        self.setProperty('basitDetailPlaceholder', True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        self.title_label = QLabel(title or translate('details'))
        self.title_label.setObjectName('DetailTitle')
        self.subtitle_label = QLabel(translate('select_record_to_preview') if translate('select_record_to_preview') != 'select_record_to_preview' else 'اختر سجلاً لعرض ملخصه')
        self.subtitle_label.setObjectName('DetailSubtitle')
        self.body_label = QLabel('')
        self.body_label.setObjectName('DetailBody')
        self.body_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.body_label, 1)
        # Phase404: DetailPlaceholder styling is centralized in theme/qss.py.

    def set_summary(self, title: str, lines: list[str]) -> None:
        self.title_label.setText(title or translate('details'))
        self.subtitle_label.setText(translate('record_preview') if translate('record_preview') != 'record_preview' else 'معاينة السجل')
        self.body_label.setText('\n'.join(str(line) for line in lines if line is not None))

    def clear_summary(self) -> None:
        self.title_label.setText(translate('details'))
        self.subtitle_label.setText(translate('select_record_to_preview') if translate('select_record_to_preview') != 'select_record_to_preview' else 'اختر سجلاً لعرض ملخصه')
        self.body_label.setText('')


class ResponsiveMasterDetail(QWidget):
    """Standard responsive shell for list/detail screens.

    The left side is the existing list widget or table area; the right side is a
    preview/editor panel. QSplitter gives users real resizing behavior instead
    of dead whitespace when the main window is enlarged.
    """

    def __init__(self, master: QWidget, detail: QWidget, parent: Optional[QWidget] = None, *, master_weight: int = 3, detail_weight: int = 2) -> None:
        super().__init__(parent)
        self.setProperty('basitMasterDetail', True)
        self.master_weight = max(1, int(master_weight or 1))
        self.detail_weight = max(1, int(detail_weight or 1))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setObjectName('ResponsiveMasterDetailSplitter')
        self.splitter.setProperty('basitMasterDetailSplitter', True)
        self.splitter.addWidget(master)
        self.splitter.addWidget(detail)
        self.splitter.setStretchFactor(0, self.master_weight)
        self.splitter.setStretchFactor(1, self.detail_weight)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter)

    def set_initial_sizes(self, total_width: int = 1200) -> None:
        total_weight = max(1, self.master_weight + self.detail_weight)
        master_width = int(total_width * self.master_weight / total_weight)
        detail_width = max(1, int(total_width) - master_width)
        self.splitter.setSizes([master_width, detail_width])
