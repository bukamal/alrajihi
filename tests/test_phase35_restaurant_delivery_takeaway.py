from pathlib import Path


def test_phase35_delivery_takeaway_boundaries_present():
    root = Path(__file__).resolve().parents[1]
    repo = (root / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    routes = (root / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    service = (root / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")

    assert "restaurant_delivery_events" in repo
    assert "create_delivery_order" in repo
    assert "create_takeaway_order" in repo
    assert "/restaurant/delivery_orders" in routes
    assert "/restaurant/takeaway_orders" in routes
    assert "def create_delivery_order" in service


def test_phase35_delivery_status_contract():
    root = Path(__file__).resolve().parents[1]
    gateway = (root / "alrajhi_client" / "gateways" / "restaurant_gateway.py").read_text(encoding="utf-8")
    remote = (root / "alrajhi_client" / "gateways" / "remote" / "restaurant_gateway.py").read_text(encoding="utf-8")
    assert "update_delivery_status" in gateway
    assert "out_for_delivery" in (root / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    assert "/delivery_status" in remote
