# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.lazy_page_factory_import_path_contract import phase443_lazy_page_factory_import_path_summary


def test_phase443_lazy_page_factory_import_path_contract():
    summary = phase443_lazy_page_factory_import_path_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["factory_specs"]["pos"]["module"] == "alrajhi_client.views.widgets.pos_widget"
    assert summary["factory_specs"]["restaurant"]["module"] == "alrajhi_client.views.restaurant.restaurant_simple_pos_widget"
    assert not summary["legacy_short_specs"]
