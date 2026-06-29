# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.windows_runtime_visual_acceptance_corrections_contract import phase453_windows_runtime_visual_acceptance_corrections_summary


def test_phase453_windows_runtime_visual_acceptance_corrections_ready():
    summary = phase453_windows_runtime_visual_acceptance_corrections_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["phase"] == 453
    assert summary["checks"] >= 50


def test_phase453_qss_runs_after_phase452():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert qss.find("Phase453: Windows runtime visual acceptance corrections") > qss.find("Phase452: dialogs and modal windows visual unification")
    assert 'QWidget[windowsRuntimeVisualAcceptancePhase="453"] QHeaderView::section' in qss


def test_phase453_invoice_and_pos_local_styles_are_suppressed():
    invoice = (ROOT / "alrajhi_client/views/dialogs/invoice_dialog.py").read_text(encoding="utf-8")
    pos_payment = (ROOT / "alrajhi_client/features/pos/pos_payment_shell.py").read_text(encoding="utf-8")
    assert "documentLocalStylesSuppressed" in invoice
    assert "QDialog {{ background:" not in invoice
    assert "ThemeManager.get('primary')" not in pos_payment
