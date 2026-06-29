# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.operational_pos_restaurant_surface_migration_contract import phase448_operational_pos_restaurant_surface_migration_summary


def test_phase448_operational_surface_ready():
    summary = phase448_operational_pos_restaurant_surface_migration_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_operational_qss_overrides_legacy_basit_skin():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert "Phase401: Basit inspired operational skin" in qss
    assert "Phase448: Operational POS/Restaurant surface migration" in qss
    assert qss.find("Phase448: Operational POS/Restaurant surface migration") > qss.find("Phase401: Basit inspired operational skin")


def test_pos_is_barcode_table_first_but_visual_identity_bound():
    pos = (ROOT / "alrajhi_client/views/widgets/pos_widget.py").read_text(encoding="utf-8")
    assert "Phase430: POS is barcode/table-first" in pos
    assert "OperationalItemCardGrid" not in pos
    assert "operational_scan_input" in pos
    assert "operational_payment_shell" in pos


def test_restaurant_surfaces_use_shared_operational_roles():
    simple = (ROOT / "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py").read_text(encoding="utf-8")
    full = (ROOT / "alrajhi_client/views/restaurant/restaurant_pos_widget.py").read_text(encoding="utf-8")
    assert "operational_section_title" in simple
    assert "operational_total" in simple
    assert "operational_actions" in full
    assert "operational_table" in full
