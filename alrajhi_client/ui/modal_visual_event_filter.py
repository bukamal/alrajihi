# -*- coding: utf-8 -*-
"""Phase452 runtime modal visual event filter.

Installs one safe QApplication-level filter that marks QDialog/QMessageBox
instances at show time.  It is deliberately cosmetic: no signals, accepted /
rejected handlers, service calls or persistence paths are changed.
"""
from __future__ import annotations

from PyQt5.QtCore import QObject, QEvent, QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from ui.dialog_branding import apply_modal_visual_template, brand_message_box


class ModalVisualEventFilter(QObject):
    """Apply Phase452 modal visual properties to dialogs created outside helpers."""

    def eventFilter(self, obj, event):  # type: ignore[override]
        try:
            if event.type() == QEvent.Show and isinstance(obj, (QDialog, QMessageBox)):
                if str(obj.property("modalVisualPhase") or "") != "452":
                    QTimer.singleShot(0, lambda target=obj: self._apply(target))
        except Exception:
            pass
        return False

    def _apply(self, target) -> None:
        try:
            if isinstance(target, QMessageBox):
                tone = str(target.property("dialogKind") or "info").replace("message_", "") or "info"
                brand_message_box(target, tone)
            else:
                role = str(target.property("dialogKind") or target.objectName() or "system")
                apply_modal_visual_template(target, role=role)
        except RuntimeError:
            pass
        except Exception:
            pass


def install_modal_visual_event_filter(app: QApplication | None = None) -> ModalVisualEventFilter | None:
    """Install the global Phase452 modal visual filter once per QApplication."""
    app = app or QApplication.instance()
    if app is None:
        return None
    existing = getattr(app, "_alrajhi_modal_visual_filter", None)
    if existing is not None:
        return existing
    filter_obj = ModalVisualEventFilter(app)
    try:
        app.installEventFilter(filter_obj)
        app._alrajhi_modal_visual_filter = filter_obj
        return filter_obj
    except Exception:
        return None


__all__ = ["ModalVisualEventFilter", "install_modal_visual_event_filter"]
