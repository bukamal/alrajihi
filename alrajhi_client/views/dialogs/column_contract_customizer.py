# -*- coding: utf-8 -*-
"""Universal column contract customizer dialog.

Phase 342 replaces screen-only column hiding in contract-backed tables with a
runtime editor for display, print and export preferences.  The dialog is used by
both SmartTableView context menus and the unified settings surface.
"""
from __future__ import annotations

from typing import Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QGridLayout,
)

from i18n import translate
from ui.dialog_branding import apply_branded_dialog, normalize_dialog_buttons
from workspace.settings.column_preferences import (
    contract_column_states,
    reset_contract_column_preferences,
    save_contract_column_preferences,
)
from workspace.tables.table_column_registry import table_column_contract_by_id


class ColumnContractCustomizerDialog(QDialog):
    def __init__(self, parent=None, contract_id: str = "", title: str = "") -> None:
        super().__init__(parent)
        self.contract = table_column_contract_by_id(contract_id)
        if self.contract is None:
            raise ValueError(f"Unknown column contract: {contract_id}")
        self.setWindowTitle(title or f"{translate('columns')} — {self.contract.contract_id}")
        self.setMinimumSize(620, 520)
        self.setProperty('brandDialog', True)
        self.setProperty('dialogKind', 'column_customizer')
        self._checks: Dict[str, Dict[str, QCheckBox]] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        hint = QLabel(translate('settings_surface_column_editor_hint'))
        hint.setWordWrap(True)
        outer.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        headers = (
            translate('settings_surface_column_label'),
            translate('settings_surface_visible_column'),
            translate('settings_surface_printable_column'),
            translate('settings_surface_exportable_column'),
        )
        for c, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet('font-weight: 800;')
            grid.addWidget(lbl, 0, c)

        for r, state in enumerate(contract_column_states(self.contract), start=1):
            label = translate(state.label_key)
            if label == state.label_key:
                label = state.label_key
            name = QLabel(label)
            name.setWordWrap(True)
            grid.addWidget(name, r, 0)
            row_checks: Dict[str, QCheckBox] = {}
            for c, purpose in enumerate(('display', 'print', 'export'), start=1):
                chk = QCheckBox()
                chk.setChecked(bool(getattr(state, purpose)))
                chk.setToolTip(state.settings.get(purpose, ''))
                if purpose == 'display' and state.required:
                    chk.setChecked(True)
                    chk.setEnabled(False)
                wrapper = QWidget()
                h = QHBoxLayout(wrapper)
                h.setContentsMargins(0, 0, 0, 0)
                h.addStretch(1)
                h.addWidget(chk)
                h.addStretch(1)
                grid.addWidget(wrapper, r, c)
                row_checks[purpose] = chk
            self._checks[state.column_key] = row_checks
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        reset = QPushButton(translate('reset_columns'))
        save = QPushButton(translate('save'))
        close = QPushButton(translate('close'))
        save.setObjectName('primary')
        reset.clicked.connect(self._reset)
        save.clicked.connect(self._save)
        close.setProperty('dialogActionRole', 'close')
        reset.setProperty('dialogActionRole', 'secondary')
        save.setProperty('dialogActionRole', 'primary')
        close.clicked.connect(self.reject)
        buttons.addWidget(reset)
        buttons.addStretch(1)
        buttons.addWidget(save)
        buttons.addWidget(close)
        outer.addLayout(buttons)
        normalize_dialog_buttons(self)
        apply_branded_dialog(self, self.windowTitle(), role='column_customizer')

    def preferences(self) -> Dict[str, Dict[str, bool]]:
        values: Dict[str, Dict[str, bool]] = {}
        for column_key, checks in self._checks.items():
            values[column_key] = {
                'display': bool(checks['display'].isChecked()),
                'print': bool(checks['print'].isChecked()),
                'export': bool(checks['export'].isChecked()),
            }
        return values

    def _save(self) -> None:
        save_contract_column_preferences(self.contract, self.preferences())
        self.accept()

    def _reset(self) -> None:
        reset_contract_column_preferences(self.contract)
        self.accept()


__all__ = ['ColumnContractCustomizerDialog']
