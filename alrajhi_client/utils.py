# -*- coding: utf-8 -*-
from core.services.settings_service import settings_service
from PyQt5.QtCore import QObject, QTimer, Qt, QEvent
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QAbstractSpinBox
try:
    from PyQt5 import sip
except Exception:  # pragma: no cover - depends on PyQt packaging
    sip = None
import re

_currency_symbol = None
_currency_decimals = None
_number_format = None

def update_currency_format():
    global _currency_symbol, _currency_decimals, _number_format
    _currency_symbol = settings_service.get('currency_symbol', '$')
    _currency_decimals = int(settings_service.get('currency_decimals', '2'))
    _number_format = settings_service.get('number_format', 'western')

def format_currency(amount: float) -> str:
    """Legacy compatibility wrapper around the unified money display policy."""
    if _currency_symbol is None:
        update_currency_format()
    try:
        from core.money_display_policy import format_money
        display_currency = settings_service.get('display_currency', 'SYP')
        return format_money(amount, display_currency, decimals=_currency_decimals)
    except Exception:
        formatted = f"{amount:,.{_currency_decimals}f}"
        if _number_format == 'arabic':
            formatted = formatted.replace('0', '٠').replace('1', '١').replace('2', '٢').replace('3', '٣').replace('4', '٤')\
                                 .replace('5', '٥').replace('6', '٦').replace('7', '٧').replace('8', '٨').replace('9', '٩')
        return f"{formatted} {_currency_symbol}"

def format_date(date_str: str) -> str:
    if not date_str:
        return ''
    import datetime
    try:
        dt = datetime.datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str

def clean_text(text: str) -> str:
    if not text:
        return ''
    text = str(text)
    bad_chars = ['浏', '�', '\u200e', '\u200f', '\ufeff', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e']
    for ch in bad_chars:
        text = text.replace(ch, '')
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9\s\-\.\,\:\;\(\)\/\+%]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def show_toast(message, msg_type='info', parent=None, duration=2600):
    """Show a non-blocking professional toast notification."""
    try:
        from views.widgets.toast_notification import ToastNotification
        target = parent or QApplication.activeWindow()
        toast = ToastNotification(message, msg_type, target, duration=duration)
        toast.show_toast()
    except Exception:
        print(f"[{msg_type}] {message}")


def install_non_blocking_message_boxes(app=None):
    """Replace OK-style QMessageBox info/warning/error with auto-dismiss toasts.

    Confirmation dialogs (QMessageBox.question) are intentionally not changed.
    """
    from PyQt5.QtWidgets import QMessageBox
    if getattr(QMessageBox, '_alrajhi_toast_patched', False):
        return

    def _toast(parent, title, message, msg_type='info', *args, **kwargs):
        show_toast(message or title, msg_type, parent)
        return QMessageBox.Ok

    QMessageBox.information = staticmethod(
        lambda parent, title, message='', *a, **k: _toast(
            parent, title, message,
            'success' if str(title).strip() in ('نجاح', 'تم الحفظ', 'تم') else 'info',
            *a, **k
        )
    )
    QMessageBox.warning = staticmethod(lambda parent, title, message='', *a, **k: _toast(parent, title, message, 'warning', *a, **k))
    QMessageBox.critical = staticmethod(lambda parent, title, message='', *a, **k: _toast(parent, title, message, 'error', *a, **k))
    QMessageBox._alrajhi_toast_patched = True


def focus_first_input(widget, delay=120):
    """Focus the first practical input field in a dialog/window."""
    def _focus():
        try:
            candidates = []
            for cls in (QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit, QTextEdit):
                candidates.extend(widget.findChildren(cls))
            # Prefer text fields, then combos, then numeric/date fields.
            candidates.sort(key=lambda w: 0 if isinstance(w, QLineEdit) else 1 if isinstance(w, QComboBox) else 2)
            for child in candidates:
                if not child.isVisible() or not child.isEnabled():
                    continue
                child.setFocus(Qt.OtherFocusReason)
                if isinstance(child, QLineEdit) and _is_qobject_alive(child):
                    child.selectAll()
                elif isinstance(child, QComboBox) and child.isEditable() and child.lineEdit() and _is_qobject_alive(child.lineEdit()):
                    child.lineEdit().selectAll()
                elif isinstance(child, (QSpinBox, QDoubleSpinBox)):
                    le = child.findChild(QLineEdit)
                    if le and _is_qobject_alive(le):
                        le.selectAll()
                return
        except Exception:
            pass
    QTimer.singleShot(delay, _focus)


def _is_qobject_alive(obj):
    """Return False when a PyQt wrapper points to a deleted C++ QObject."""
    if obj is None:
        return False
    try:
        if sip is not None and sip.isdeleted(obj):
            return False
        # Touch a harmless QObject method so deleted wrappers raise RuntimeError here, not later.
        obj.objectName()
        return True
    except RuntimeError:
        return False
    except Exception:
        # Non-QObject or unusual widgets should not break focus handling.
        return True

# ========== تحديد النص تلقائياً ==========
class AutoSelectManager(QObject):
    """Global text-focus policy.

    Phase 348 makes text focus predictable across Arabic/English/German forms:
    focus selects the current text, mouse-clicking an already focused input also
    selects it, and editable combo/spinbox line edits follow the same rule.
    """

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.app.focusChanged.connect(self.on_focus_changed)
        try:
            self.app.installEventFilter(self)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            etype = event.type()
            if etype in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
                line_edit = self._get_line_edit(obj)
                if line_edit and _is_qobject_alive(line_edit):
                    QTimer.singleShot(0, lambda le=line_edit: self._select_all(le))
            elif etype == QEvent.FocusIn:
                line_edit = self._get_line_edit(obj)
                if line_edit and _is_qobject_alive(line_edit):
                    QTimer.singleShot(0, lambda le=line_edit: self._select_all(le))
        except Exception:
            pass
        return False

    def on_focus_changed(self, old, new):
        if new is None:
            return
        line_edit = self._get_line_edit(new)
        if line_edit and _is_qobject_alive(line_edit):
            QTimer.singleShot(80, lambda le=line_edit: self._select_all(le))

    def _get_line_edit(self, widget):
        if isinstance(widget, QLineEdit):
            return widget
        elif isinstance(widget, QTextEdit):
            return widget
        elif isinstance(widget, QComboBox) and widget.isEditable():
            return widget.lineEdit()
        elif isinstance(widget, QDateEdit):
            return widget.findChild(QLineEdit)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.findChild(QLineEdit)
        return None

    def _select_all(self, line_edit):
        if not _is_qobject_alive(line_edit):
            return
        try:
            if hasattr(line_edit, 'selectAll'):
                line_edit.selectAll()
        except RuntimeError:
            return

def enable_auto_select_all(app):
    manager = AutoSelectManager(app)
    app.auto_select_manager = manager
    print("✅ تم تفعيل تحديد النص تلقائياً عند التركيز والنقر")
