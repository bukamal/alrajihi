# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"PHASE177 GUARD FAILED: {message}")


pos_widget = read('alrajhi_client/views/widgets/pos_widget.py')
payment_shell = read('alrajhi_client/features/pos/pos_payment_shell.py')
translator = read('alrajhi_client/i18n/translator.py')

require('from features.pos.pos_payment_shell import POSPaymentShell' in pos_widget, 'POSWidget must import POSPaymentShell')
require('self.payment_shell = POSPaymentShell' in pos_widget, 'POSWidget must instantiate POSPaymentShell')
require('summary_row = QHBoxLayout()' not in pos_widget, 'legacy inline POS summary row must be removed')
require('buttons = QHBoxLayout()' not in pos_widget, 'legacy inline POS action row must be removed')
require('class POSPaymentShell' in payment_shell, 'POSPaymentShell class is missing')
require('payment_combo = QComboBox' in payment_shell, 'payment combo must live in POSPaymentShell')
require('paid_spin = QDoubleSpinBox' in payment_shell, 'paid spin must live in POSPaymentShell')
require('apply_density' in payment_shell, 'POSPaymentShell must support touch density')
require('pos_payment_shell_title' in translator, 'POS payment shell translations are missing')
require('pos_total_card' in translator and 'pos_change_card' in translator, 'POS payment metric translations are missing')
print('PHASE177 POS PAYMENT SHELL GUARD PASSED')
