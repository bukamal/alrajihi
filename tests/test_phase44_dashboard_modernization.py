from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_modern_components_parse_and_are_used():
    components = ROOT / "alrajhi_client" / "ui" / "dashboard_components.py"
    dashboard = ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py"
    ast.parse(components.read_text(encoding="utf-8"))
    source = dashboard.read_text(encoding="utf-8")
    ast.parse(source)
    assert "ModernKpiCard" in source
    assert "DashboardChartPanel" in source
    assert "_build_kpi_grid()" in source
    assert "printing_service" not in source


def test_dashboard_components_keep_service_boundary():
    source = (ROOT / "alrajhi_client" / "ui" / "dashboard_components.py").read_text(encoding="utf-8")
    forbidden = ["DatabaseConnection", "sqlite3", ".execute(", ".query("]
    assert not any(token in source for token in forbidden)
