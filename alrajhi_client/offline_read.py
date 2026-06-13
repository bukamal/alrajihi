# -*- coding: utf-8 -*-
"""Utilities for graceful handling of remote read failures in client/offline mode."""
from __future__ import annotations

OFFLINE_READ_MARKERS = (
    'No connection and this operation cannot be queued safely',
    'Connection refused',
    'Max retries exceeded',
    'Failed to establish a new connection',
    'ConnectionError',
    'Read timed out',
    'ConnectTimeout',
)


def is_offline_read_error(exc) -> bool:
    text = str(exc or '')
    return any(marker in text for marker in OFFLINE_READ_MARKERS)


def offline_read_message(context: str | None = None) -> str:
    base = 'تعذر تحديث البيانات لأن الخادم غير متصل. ستبقى العمليات المحفوظة Offline في قائمة المزامنة.'
    return f'{context}: {base}' if context else base


def notify_offline_read(parent=None, context: str | None = None):
    msg = offline_read_message(context)
    try:
        from utils import show_toast
        show_toast(msg, 'warning', parent)
        return
    except Exception:
        pass
    try:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(parent, 'وضع عدم الاتصال', msg)
    except Exception:
        try:
            print(f'⚠️ {msg}')
        except Exception:
            pass


def install_offline_exception_hook(app=None):
    """Prevent known offline read exceptions from aborting PyQt signal handlers."""
    import sys
    old_hook = getattr(sys, 'excepthook', None)

    def _hook(exc_type, exc, tb):
        if is_offline_read_error(exc):
            try:
                print(f'⚠️ Offline read suppressed: {exc}')
            except Exception:
                pass
            try:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, lambda: notify_offline_read(None))
            except Exception:
                notify_offline_read(None)
            return
        if old_hook:
            return old_hook(exc_type, exc, tb)
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook
