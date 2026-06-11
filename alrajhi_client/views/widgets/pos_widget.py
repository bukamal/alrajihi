# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QDoubleSpinBox, QShortcut, QInputDialog
)
import qtawesome as qta

from core.services.pos_service import pos_service, POSException
from core.services.warehouse_service import warehouse_service
from core.services.cashbox_service import cashbox_service
from core.services.settings_service import settings_service
from currency import currency
from utils import show_toast


class POSWidget(QWidget):
    """Fast barcode sale screen for cashier-style workflows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.cart = pos_service.new_cart(self._selected_warehouse_id() if hasattr(self, 'warehouse_combo') else None, self._selected_cashbox_id() if hasattr(self, 'cashbox_combo') else None)
        self.display_curr = currency.get_display_currency()
        self._init_ui()
        self._setup_shortcuts()
        self.refresh_cart()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("🧾 نقطة البيع السريعة POS")
        title.setStyleSheet("font-size: 24px; font-weight: 800;")
        title_row.addWidget(title)
        title_row.addStretch()
        self.fullscreen_btn = QPushButton("ملء الشاشة")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        title_row.addWidget(self.fullscreen_btn)
        layout.addLayout(title_row)

        hint = QLabel("امسح الباركود مباشرة. F2 نقدي، F3 بطاقة، F10 إنهاء، Ctrl+L للعودة لحقل المسح.")
        hint.setObjectName("muted")
        layout.addWidget(hint)

        wh_row = QHBoxLayout()
        wh_row.addWidget(QLabel("مستودع الصرف:"))
        self.warehouse_combo = QComboBox()
        self._load_warehouses()
        self.warehouse_combo.currentIndexChanged.connect(self.on_warehouse_changed)
        wh_row.addWidget(self.warehouse_combo, 1)
        layout.addLayout(wh_row)

        shift_row = QHBoxLayout()
        shift_row.addWidget(QLabel("الصندوق:"))
        self.cashbox_combo = QComboBox()
        self._load_cashboxes()
        self.cashbox_combo.currentIndexChanged.connect(self.on_cashbox_changed)
        shift_row.addWidget(self.cashbox_combo, 1)
        self.shift_label = QLabel("لا توجد وردية مفتوحة")
        self.shift_label.setObjectName("muted")
        shift_row.addWidget(self.shift_label, 1)
        self.open_shift_btn = QPushButton("فتح وردية")
        self.open_shift_btn.clicked.connect(self.open_shift)
        self.close_shift_btn = QPushButton("إغلاق وردية")
        self.close_shift_btn.clicked.connect(self.close_shift)
        shift_row.addWidget(self.open_shift_btn)
        shift_row.addWidget(self.close_shift_btn)
        layout.addLayout(shift_row)
        self._shift_row_widgets = [self.shift_label, self.open_shift_btn, self.close_shift_btn]
        self._apply_shift_mode_visibility()

        scan_row = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("امسح الباركود أو اكتب الكود ثم Enter...")
        self.barcode_input.setMinimumHeight(60)
        self.barcode_input.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px;")
        self.barcode_input.returnPressed.connect(self.scan_entered_barcode)
        scan_row.addWidget(self.barcode_input, 1)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.001, 999999)
        self.qty_spin.setDecimals(3)
        self.qty_spin.setValue(1)
        self.qty_spin.setPrefix("كمية ")
        scan_row.addWidget(self.qty_spin)

        camera_btn = QPushButton("📷 مسح")
        camera_btn.clicked.connect(self.scan_with_camera)
        scan_row.addWidget(camera_btn)
        layout.addLayout(scan_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["المادة", "الباركود", "الوحدة", "الكمية", "السعر", "الإجمالي", "المتاح"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

        summary_row = QHBoxLayout()
        self.total_label = QLabel("الإجمالي: 0")
        self.total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2563eb;")
        summary_row.addWidget(self.total_label)
        summary_row.addStretch()

        self.payment_combo = QComboBox()
        self.payment_combo.addItem("نقدي", "cash")
        self.payment_combo.addItem("بطاقة", "card")
        self.payment_combo.addItem("آجل", "credit")
        self.payment_combo.currentIndexChanged.connect(self.on_payment_method_changed)
        summary_row.addWidget(QLabel("طريقة الدفع:"))
        summary_row.addWidget(self.payment_combo)

        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 999999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setPrefix("مدفوع ")
        self.paid_spin.valueChanged.connect(self.update_change_due)
        summary_row.addWidget(self.paid_spin)
        self.change_label = QLabel("الباقي: 0")
        self.change_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669;")
        summary_row.addWidget(self.change_label)
        layout.addLayout(summary_row)

        buttons = QHBoxLayout()
        self.cash_btn = QPushButton("F2 نقدي كامل")
        self.cash_btn.setObjectName("primary")
        self.cash_btn.clicked.connect(self.pay_cash_full)
        buttons.addWidget(self.cash_btn)

        self.card_btn = QPushButton("F3 بطاقة")
        self.card_btn.clicked.connect(self.pay_card_full)
        buttons.addWidget(self.card_btn)

        self.suspend_btn = QPushButton("F4 تعليق")
        self.suspend_btn.clicked.connect(self.suspend_cart)
        buttons.addWidget(self.suspend_btn)

        self.resume_btn = QPushButton("F5 استرجاع")
        self.resume_btn.clicked.connect(self.resume_cart)
        buttons.addWidget(self.resume_btn)

        self.remove_btn = QPushButton("Delete حذف سطر")
        self.remove_btn.setObjectName("danger")
        self.remove_btn.clicked.connect(self.remove_selected_line)
        buttons.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("Esc إلغاء السلة")
        self.clear_btn.clicked.connect(self.clear_cart)
        buttons.addWidget(self.clear_btn)

        self.checkout_btn = QPushButton("F10 إنهاء البيع")
        self.checkout_btn.setObjectName("primary")
        self.checkout_btn.clicked.connect(self.checkout)
        buttons.addWidget(self.checkout_btn)
        layout.addLayout(buttons)

        self.status_label = QLabel("جاهز للمسح")
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)



    def _pos_shifts_enabled(self):
        try:
            return settings_service.pos_shifts_enabled()
        except Exception:
            return False

    def _apply_shift_mode_visibility(self):
        enabled = self._pos_shifts_enabled()
        for widget in getattr(self, '_shift_row_widgets', []):
            widget.setVisible(enabled)
        if hasattr(self, 'shift_label') and not enabled:
            self.shift_label.setText('الورديات معطلة - البيع يسجل مباشرة على الصندوق')

    def _load_cashboxes(self):
        self.cashbox_combo.clear()
        try:
            default_id = cashbox_service.default_cashbox_id()
            for cb in cashbox_service.cashboxes():
                self.cashbox_combo.addItem(cb.get('name', f"#{cb.get('id')}"), cb.get('id'))
                if default_id and int(cb.get('id')) == int(default_id):
                    self.cashbox_combo.setCurrentIndex(self.cashbox_combo.count() - 1)
        except Exception:
            pass
        self.refresh_shift_state()

    def _selected_cashbox_id(self):
        try:
            return int(self.cashbox_combo.currentData() or 0) or None
        except Exception:
            return None

    def refresh_shift_state(self):
        try:
            if not self._pos_shifts_enabled():
                self.current_shift_id = None
                if hasattr(self, 'shift_label'):
                    self.shift_label.setText('الورديات معطلة - البيع مباشر على الصندوق')
                if hasattr(self, 'open_shift_btn'):
                    self.open_shift_btn.setEnabled(False)
                if hasattr(self, 'close_shift_btn'):
                    self.close_shift_btn.setEnabled(False)
                if hasattr(self, 'checkout_btn'):
                    self.checkout_btn.setEnabled(bool(getattr(self, 'cart', None) and self.cart.lines))
                return

            shift = cashbox_service.current_open_shift(self._selected_cashbox_id())
            if shift:
                self.current_shift_id = shift.get('id')
                self.shift_label.setText(f"وردية مفتوحة #{shift.get('id')} - {shift.get('cashbox_name','')}")
                self.open_shift_btn.setEnabled(False)
                self.close_shift_btn.setEnabled(True)
            else:
                self.current_shift_id = None
                self.shift_label.setText('لا توجد وردية مفتوحة')
                self.open_shift_btn.setEnabled(True)
                self.close_shift_btn.setEnabled(False)
            if hasattr(self, 'checkout_btn'):
                self.checkout_btn.setEnabled(bool(getattr(self, 'cart', None) and self.cart.lines) and bool(getattr(self, 'current_shift_id', None)))
        except Exception:
            pass

    def on_cashbox_changed(self):
        if getattr(self, 'cart', None) and self.cart.lines:
            reply = QMessageBox.question(self, "تغيير الصندوق", "سيتم تفريغ السلة عند تغيير الصندوق. هل تريد المتابعة؟", QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.cart = pos_service.new_cart(self._selected_warehouse_id(), self._selected_cashbox_id())
        self.refresh_cart()
        self.refresh_shift_state()
        self.barcode_input.setFocus()

    def open_shift(self):
        cashbox_id = self._selected_cashbox_id()
        if not cashbox_id:
            QMessageBox.warning(self, "وردية", "اختر صندوقاً أولاً")
            return
        opening, ok = QInputDialog.getDouble(self, "فتح وردية", "الرصيد الافتتاحي:", 0, 0, 999999999, 2)
        if not ok:
            return
        try:
            sid = cashbox_service.open_shift({'cashbox_id': cashbox_id, 'opening_amount': Decimal(str(opening))})
            self.cart = pos_service.new_cart(self._selected_warehouse_id(), cashbox_id, sid)
            self.refresh_shift_state()
            show_toast("تم فتح الوردية", "success", self)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
        self.barcode_input.setFocus()

    def close_shift(self):
        shift = cashbox_service.current_open_shift(self._selected_cashbox_id())
        if not shift:
            QMessageBox.information(self, "إغلاق وردية", "لا توجد وردية مفتوحة")
            return
        try:
            summary = cashbox_service.shift_summary(shift['id'])
            expected = Decimal(str(summary.get('expected_amount') or 0))
        except Exception:
            expected = Decimal('0')
        actual, ok = QInputDialog.getDouble(self, "إغلاق وردية", f"الرصيد المتوقع: {currency.format_amount(currency.convert(expected, 'USD', self.display_curr))}\nأدخل الرصيد الفعلي:", float(currency.convert(expected, 'USD', self.display_curr)), 0, 999999999, 2)
        if not ok:
            return
        try:
            actual_usd = currency.convert(Decimal(str(actual)), self.display_curr, 'USD')
            summary = cashbox_service.close_shift(shift['id'], actual_usd)
            diff = Decimal(str(summary.get('difference_amount') or 0))
            QMessageBox.information(self, "تقرير إغلاق الوردية", f"تم إغلاق الوردية #{shift['id']}\nالمبيعات: {summary.get('total_sales')}\nالنقد: {summary.get('total_cash')}\nالبطاقة: {summary.get('total_card')}\nالفرق: {diff}")
            self.cart = pos_service.new_cart(self._selected_warehouse_id(), self._selected_cashbox_id())
            self.refresh_shift_state()
            self.refresh_cart()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
        self.barcode_input.setFocus()

    def _load_warehouses(self):
        self.warehouse_combo.clear()
        try:
            default_id = warehouse_service.default_warehouse_id()
            for wh in warehouse_service.warehouses():
                self.warehouse_combo.addItem(wh.get('name', f"#{wh.get('id')}"), wh.get('id'))
                if default_id and int(wh.get('id')) == int(default_id):
                    self.warehouse_combo.setCurrentIndex(self.warehouse_combo.count() - 1)
        except Exception:
            pass

    def _selected_warehouse_id(self):
        try:
            return int(self.warehouse_combo.currentData() or 0) or None
        except Exception:
            return None

    def on_warehouse_changed(self):
        new_id = self._selected_warehouse_id()
        if self.cart.lines:
            reply = QMessageBox.question(self, "تغيير المستودع", "سيتم تفريغ السلة عند تغيير مستودع الصرف. هل تريد المتابعة؟", QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.cart = pos_service.new_cart(new_id, self._selected_cashbox_id())
        self.refresh_cart()
        self.barcode_input.setFocus()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F2"), self, self.pay_cash_full)
        QShortcut(QKeySequence("F3"), self, self.pay_card_full)
        QShortcut(QKeySequence("F4"), self, self.suspend_cart)
        QShortcut(QKeySequence("F5"), self, self.resume_cart)
        QShortcut(QKeySequence("F10"), self, self.checkout)
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_line)
        QShortcut(QKeySequence("Escape"), self, self.clear_cart)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self.barcode_input.setFocus())
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)

    def scan_entered_barcode(self):
        code = self.barcode_input.text().strip()
        self.add_barcode_to_cart(code)

    def scan_with_camera(self):
        try:
            from views.dialogs.barcode_camera_dialog import BarcodeCameraDialog
            dialog = BarcodeCameraDialog(self)
            dialog.barcode_scanned.connect(lambda value, sym=None: self.add_barcode_to_cart(value))
            dialog.exec()
        except Exception as e:
            show_toast(f"تعذر تشغيل الكاميرا: {e}", "warning", self)
            self.barcode_input.setFocus()

    def add_barcode_to_cart(self, code):
        try:
            line = pos_service.add_scan(self.cart, code, Decimal(str(self.qty_spin.value())))
            self.status_label.setText(f"تمت إضافة/تحديث: {line.name}")
            self.barcode_input.clear()
            self.qty_spin.setValue(1)
            self.refresh_cart()
            show_toast("تمت إضافة المادة", "success", self)
        except POSException as e:
            show_toast(str(e), "error", self)
        except Exception as e:
            show_toast(f"خطأ في المسح: {e}", "error", self)
        finally:
            self.barcode_input.setFocus()

    def refresh_cart(self):
        self.table.setRowCount(0)
        for row, line in enumerate(self.cart.lines):
            self.table.insertRow(row)
            price = currency.convert(line.unit_price_usd, 'USD', self.display_curr)
            total = currency.convert(line.total_usd, 'USD', self.display_curr)
            available = line.available_qty
            values = [line.name, line.barcode, line.unit, str(line.qty), currency.format_amount(price), currency.format_amount(total), str(available)]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            if line.qty >= available and available > 0:
                for col in range(self.table.columnCount()):
                    self.table.item(row, col).setToolTip("تنبيه: الكمية المباعة تساوي أو تتجاوز المتاح")
        total_display = currency.convert(self.cart.total_usd, 'USD', self.display_curr)
        self.total_label.setText(f"الإجمالي: {currency.format_amount(total_display)}")
        if self.payment_combo.currentData() in ('cash', 'card'):
            self.paid_spin.setValue(float(total_display))
        self.update_change_due()
        self.refresh_shift_state()
        self.checkout_btn.setEnabled(bool(self.cart.lines) and (not self._pos_shifts_enabled() or bool(getattr(self, 'current_shift_id', None))))

    def update_change_due(self):
        try:
            paid_display = Decimal(str(self.paid_spin.value()))
            total_display = currency.convert(self.cart.total_usd, 'USD', self.display_curr)
            change = paid_display - total_display
            if change > 0:
                self.change_label.setText(f"الباقي للزبون: {currency.format_amount(change)}")
                self.change_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669;")
            elif change < 0:
                self.change_label.setText(f"المتبقي: {currency.format_amount(abs(change))}")
                self.change_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #dc2626;")
            else:
                self.change_label.setText("الباقي: 0")
                self.change_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669;")
        except Exception:
            pass

    def toggle_fullscreen(self):
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
            self.fullscreen_btn.setText("ملء الشاشة")
        else:
            window.showFullScreen()
            self.fullscreen_btn.setText("خروج من ملء الشاشة")
        self.barcode_input.setFocus()

    def on_payment_method_changed(self):
        if self.payment_combo.currentData() == 'credit':
            self.paid_spin.setValue(0)
        else:
            total_display = currency.convert(self.cart.total_usd, 'USD', self.display_curr)
            self.paid_spin.setValue(float(total_display))

    def pay_cash_full(self):
        self.payment_combo.setCurrentIndex(0)
        self.on_payment_method_changed()

    def pay_card_full(self):
        self.payment_combo.setCurrentIndex(1)
        self.on_payment_method_changed()

    def remove_selected_line(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.cart.lines):
            return
        item_id = self.cart.lines[row].item_id
        pos_service.remove_line(self.cart, item_id)
        self.refresh_cart()
        self.barcode_input.setFocus()

    def clear_cart(self):
        if not self.cart.lines:
            self.barcode_input.setFocus()
            return
        reply = QMessageBox.question(self, "إلغاء البيع", "هل تريد إلغاء السلة الحالية؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            pos_service.clear(self.cart)
            self.refresh_cart()
            self.status_label.setText("تم إلغاء السلة")
            self.barcode_input.setFocus()

    def suspend_cart(self):
        try:
            note, ok = QInputDialog.getText(self, "تعليق البيع", "ملاحظة البيع المعلق:")
            if not ok:
                return
            pos_service.suspend(self.cart, note)
            self.cart = pos_service.new_cart(self._selected_warehouse_id() if hasattr(self, 'warehouse_combo') else None, self._selected_cashbox_id() if hasattr(self, 'cashbox_combo') else None)
            self.refresh_cart()
            show_toast("تم تعليق البيع", "success", self)
        except POSException as e:
            show_toast(str(e), "warning", self)
        finally:
            self.barcode_input.setFocus()

    def resume_cart(self):
        if not pos_service.suspended_carts:
            show_toast("لا توجد مبيعات معلقة", "info", self)
            return
        labels = [f"{i+1}. {cart.note or cart.created_at} - {currency.format_amount(currency.convert(cart.total_usd, 'USD', self.display_curr))}" for i, cart in enumerate(pos_service.suspended_carts)]
        choice, ok = QInputDialog.getItem(self, "استرجاع بيع معلق", "اختر السلة:", labels, 0, False)
        if not ok:
            return
        index = labels.index(choice)
        try:
            if self.cart.lines:
                pos_service.suspend(self.cart, "سلة حالية قبل الاسترجاع")
            self.cart = pos_service.resume(index)
            self.refresh_cart()
            show_toast("تم استرجاع البيع", "success", self)
        except POSException as e:
            show_toast(str(e), "error", self)
        finally:
            self.barcode_input.setFocus()

    def checkout(self):
        try:
            self.refresh_shift_state()
            if self._pos_shifts_enabled() and not getattr(self, 'current_shift_id', None):
                raise POSException('افتح وردية قبل إنهاء البيع')
            payment_method = self.payment_combo.currentData() or 'cash'
            paid_display = Decimal(str(self.paid_spin.value()))
            paid_usd = currency.convert(paid_display, self.display_curr, 'USD')
            if payment_method in ('cash', 'card') and paid_usd < self.cart.total_usd:
                reply = QMessageBox.question(self, "مدفوع غير كامل", "المبلغ المدفوع أقل من إجمالي البيع. هل تريد المتابعة كبيع جزئي؟", QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            invoice_id = pos_service.checkout(self.cart, payment_method, paid_usd)
            show_toast(f"تم إنهاء البيع وإنشاء فاتورة رقم {invoice_id}", "success", self)
            self._offer_print_receipt(invoice_id)
            self.cart = pos_service.new_cart(self._selected_warehouse_id() if hasattr(self, 'warehouse_combo') else None, self._selected_cashbox_id() if hasattr(self, 'cashbox_combo') else None)
            self.refresh_cart()
        except POSException as e:
            show_toast(str(e), "error", self)
        except Exception as e:
            show_toast(f"فشل إنهاء البيع: {e}", "error", self)
        finally:
            self.barcode_input.setFocus()

    def _offer_print_receipt(self, invoice_id):
        reply = QMessageBox.question(self, "طباعة إيصال", "هل تريد طباعة إيصال حراري؟", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            from core.services.invoice_service import invoice_service
            from printing.printing_service import printing_service
            inv = invoice_service.get(invoice_id)
            if inv:
                printing_service.invoice_preview(inv, self, paper='thermal80')
        except Exception as e:
            show_toast(f"تعذر طباعة الإيصال: {e}", "warning", self)

    def showEvent(self, event):
        super().showEvent(event)
        self.barcode_input.setFocus()
