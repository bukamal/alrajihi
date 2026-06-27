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
    """Prevent known offline read exceptions from aborting PyQt signal handlers.

    Phase 393 hardening: installing the hook must be idempotent.  A repeated
    installation used to wrap our own hook again; if a later UI signal raised a
    RecursionError, sys.excepthook could recurse while reporting the original
    exception and flood the console.
    """
    import sys

    current_hook = getattr(sys, 'excepthook', None)
    if getattr(current_hook, '_alrajhi_offline_hook', False):
        return current_hook

    old_hook = current_hook if current_hook is not None else sys.__excepthook__
    in_hook = {'active': False}

    def _hook(exc_type, exc, tb):
        if in_hook.get('active'):
            return sys.__excepthook__(exc_type, exc, tb)
        in_hook['active'] = True
        try:
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
            # Never forward RecursionError through a chain of hook wrappers.
            # Use Python's original hook so the real stack is visible and the
            # hook itself cannot become the source of another RecursionError.
            if exc_type is RecursionError or isinstance(exc, RecursionError):
                return sys.__excepthook__(exc_type, exc, tb)
            if old_hook and old_hook is not _hook and not getattr(old_hook, '_alrajhi_offline_hook', False):
                return old_hook(exc_type, exc, tb)
            return sys.__excepthook__(exc_type, exc, tb)
        finally:
            in_hook['active'] = False

    _hook._alrajhi_offline_hook = True  # type: ignore[attr-defined]
    _hook._alrajhi_previous_hook = old_hook  # type: ignore[attr-defined]
    sys.excepthook = _hook
    return _hook
