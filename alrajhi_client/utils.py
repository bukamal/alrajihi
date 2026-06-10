# -*- coding: utf-8 -*-
from core.services.settings_service import settings_service
from PyQt5.QtCore import QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QAbstractSpinBox
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
    if _currency_symbol is None:
        update_currency_format()
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

def show_toast(message, msg_type='info', parent=None):
    try:
        from views.widgets.toast_notification import ToastNotification
        if parent:
            toast = ToastNotification(message, msg_type, parent)
            toast.show_toast()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(parent, "معلومة", message)
    except ImportError:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(parent, "معلومة", message)

# ========== تحديد النص تلقائياً ==========
class AutoSelectManager(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.app.focusChanged.connect(self.on_focus_changed)

    def on_focus_changed(self, old, new):
        if new is None:
            return
        line_edit = self._get_line_edit(new)
        if line_edit:
            QTimer.singleShot(100, lambda: self._select_all(line_edit))

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
        if line_edit and hasattr(line_edit, 'selectAll'):
            line_edit.selectAll()

def enable_auto_select_all(app):
    manager = AutoSelectManager(app)
    app.auto_select_manager = manager
    print("✅ تم تفعيل تحديد النص تلقائياً عند التركيز")


