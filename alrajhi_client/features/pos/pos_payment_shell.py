# -*- coding: utf-8 -*-
from __future__ import annotations

"""Touch payment shell for the POS screen.

This component intentionally contains presentation wiring only.  It does not
perform checkout, cashbox writes, receipt printing, or direct settings/API work;
those responsibilities remain in POSWidget/POSService and the project services.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
)

from i18n import translate


class POSPaymentShell(QWidget):
    """Payment/total/actions panel optimized for touch POS usage."""

    def __init__(self, host, parent=None):
        super().__init__(parent or host)
        self.host = host
        self.setObjectName("posPaymentShell")
        self.setProperty("visualRole", "operational_payment_shell")
        self.setProperty("operationalSurfacePhase", 448)
        self.setProperty("windowsRuntimeVisualAcceptancePhase", 453)
        self.setProperty("posPaymentCompactPhase", 469)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(5)

        header = QLabel(translate("pos_payment_shell_title"))
        header.setObjectName("sectionTitle")
        header.setProperty("visualRole", "operational_section_title")
        root.addWidget(header)
        header.setVisible(False)  # Phase469: compact sticky POS footer; title consumes cashier space.

        totals = QHBoxLayout()
        totals.setSpacing(6)

        self.total_label = self._metric_label(translate("total_zero"), "total")
        self.change_label = self._metric_label(translate("change_zero"), "change")
        totals.addWidget(self._metric_card(translate("pos_total_card"), self.total_label), 2)
        totals.addWidget(self._metric_card(translate("pos_change_card"), self.change_label), 2)

        payment_card = QWidget(self)
        payment_card.setObjectName("posPaymentCard")
        payment_card.setProperty("visualRole", "operational_panel")
        payment_layout = QHBoxLayout(payment_card)
        payment_layout.setContentsMargins(8, 6, 8, 6)
        payment_layout.setSpacing(6)
        payment_layout.addWidget(QLabel(translate("payment_method")))
        self.payment_combo = QComboBox(payment_card)
        self.payment_combo.setProperty("visualRole", "operational_select")
        self.payment_combo.addItem(translate("payment_cash"), "cash")
        self.payment_combo.addItem(translate("payment_card"), "card")
        self.payment_combo.addItem(translate("payment_credit"), "credit")
        payment_layout.addWidget(self.payment_combo, 1)
        self.paid_spin = QDoubleSpinBox(payment_card)
        self.paid_spin.setProperty("visualRole", "operational_spin")
        self.paid_spin.setRange(0, 999999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setPrefix(translate("paid_prefix"))
        payment_layout.addWidget(self.paid_spin, 1)
        totals.addWidget(payment_card, 3)
        root.addLayout(totals)

        actions = QGridLayout()
        actions.setSpacing(6)

        self.cash_btn = self._action_button("pos_cash_full_btn", primary=True)
        self.card_btn = self._action_button("pos_card_btn")
        self.checkout_btn = self._action_button("pos_checkout_btn", primary=True)
        self.suspend_btn = self._action_button("pos_suspend_btn")
        self.resume_btn = self._action_button("pos_resume_btn")
        self.remove_btn = self._action_button("pos_delete_line_btn", danger=True)
        self.clear_btn = self._action_button("pos_clear_cart_btn")

        # Phase469: one compact action row prevents the footer from being cut on
        # 1024x768 cashier screens after global chrome and tab bars are present.
        for index, button in enumerate((
            self.cash_btn, self.card_btn, self.checkout_btn, self.suspend_btn,
            self.resume_btn, self.remove_btn, self.clear_btn,
        )):
            actions.addWidget(button, 0, index)
        root.addLayout(actions)

    def _metric_label(self, text: str, role: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(f"posMetric_{role}")
        label.setProperty("visualRole", "operational_metric_value")
        label.setProperty("metricRole", role)
        label.setProperty("metricRuntimeStyle", "centralized")
        return label

    def _metric_card(self, title: str, value_label: QLabel) -> QWidget:
        card = QWidget(self)
        card.setObjectName("posMetricCard")
        card.setProperty("visualRole", "operational_panel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("muted")
        title_label.setProperty("visualRole", "operational_muted")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return card

    def _action_button(self, key: str, *, primary: bool = False, danger: bool = False) -> QPushButton:
        button = QPushButton(translate(key), self)
        if primary:
            button.setObjectName("primary")
            button.setProperty("visualRole", "operational_primary")
        elif danger:
            button.setObjectName("danger")
            button.setProperty("visualRole", "operational_danger")
        else:
            button.setProperty("visualRole", "operational_secondary")
        return button

    def apply_density(self, density: str) -> None:
        density = str(density or "touch").lower()
        if density == "compact":
            button_h, spin_h, total_px, change_px = 32, 34, 18, 16
        elif density == "comfortable":
            button_h, spin_h, total_px, change_px = 38, 40, 21, 17
        else:
            button_h, spin_h, total_px, change_px = 44, 42, 24, 18

        for name in (
            "cash_btn",
            "card_btn",
            "checkout_btn",
            "suspend_btn",
            "resume_btn",
            "remove_btn",
            "clear_btn",
        ):
            button = getattr(self, name, None)
            if button is not None:
                button.setMinimumHeight(button_h)

        self.paid_spin.setMinimumHeight(spin_h)
        self.payment_combo.setMinimumHeight(spin_h)
        self.total_label.setProperty("metricSizePx", total_px)
        self.change_label.setProperty("metricSizePx", change_px)
