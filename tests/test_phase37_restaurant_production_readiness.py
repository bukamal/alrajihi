from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_restaurant_readiness_boundary_is_exposed():
    repo = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    route = (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    contract = (ROOT / "alrajhi_client" / "gateways" / "restaurant_gateway.py").read_text(encoding="utf-8")
    service = (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")
    assert "def restaurant_production_readiness" in repo
    assert "/restaurant/readiness" in route
    assert "def restaurant_production_readiness" in contract
    assert "def restaurant_production_readiness" in service


def test_restaurant_readiness_covers_critical_tables():
    repo = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    for table in [
        "restaurant_tables",
        "restaurant_sessions",
        "restaurant_order_lines",
        "kitchen_tickets",
        "restaurant_print_jobs",
        "restaurant_inventory_consumption",
        "restaurant_orders",
        "restaurant_split_bills",
    ]:
        assert table in repo


def test_restaurant_production_readiness_guard_passes():
    result = subprocess.run(
        [sys.executable, "tools/restaurant_production_readiness_guard.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
