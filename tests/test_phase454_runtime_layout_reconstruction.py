# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.runtime_layout_reconstruction_contract import phase454_runtime_layout_reconstruction_summary


def test_phase454_runtime_layout_reconstruction_ready():
    summary = phase454_runtime_layout_reconstruction_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["phase"] == 454
    assert summary["checks"] >= 45


def test_phase454_qss_after_phase453():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert qss.find("Phase454: Runtime layout reconstruction") > qss.find("Phase453: Windows runtime visual acceptance corrections")


def test_phase454_core_screens_are_marked():
    login = (ROOT / "alrajhi_client/views/dialogs/login_dialog.py").read_text(encoding="utf-8")
    pos = (ROOT / "alrajhi_client/views/widgets/pos_widget.py").read_text(encoding="utf-8")
    invoice = (ROOT / "alrajhi_client/views/dialogs/invoice_dialog.py").read_text(encoding="utf-8")
    material = (ROOT / "alrajhi_client/features/items/item_editor_tab.py").read_text(encoding="utf-8")
    assert "loginRuntimeReconstructionPhase" in login
    assert "posRuntimeLayoutReconstructionPhase" in pos
    assert "invoiceRuntimeLayoutReconstructionPhase" in invoice
    assert "materialRuntimeLayoutReconstructionPhase" in material
