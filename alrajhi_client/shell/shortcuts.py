# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut, QWidget


def bind_workspace_shortcuts(parent: QWidget, workspace) -> list[QShortcut]:
    shortcuts = []
    close_tab = QShortcut(QKeySequence("Ctrl+W"), parent)
    close_tab.activated.connect(workspace.close_current_tab)
    shortcuts.append(close_tab)
    return shortcuts
