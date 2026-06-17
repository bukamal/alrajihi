from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SNIPPETS = {
    "server_repo_readiness": (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py", "def restaurant_production_readiness"),
    "server_route_readiness": (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py", "/restaurant/readiness"),
    "gateway_contract_readiness": (ROOT / "alrajhi_client" / "gateways" / "restaurant_gateway.py", "def restaurant_production_readiness"),
    "local_gateway_readiness": (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py", "def restaurant_production_readiness"),
    "remote_gateway_readiness": (ROOT / "alrajhi_client" / "gateways" / "remote" / "restaurant_gateway.py", "/api/restaurant/readiness"),
    "service_readiness": (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py", "def restaurant_production_readiness"),
}


def main() -> int:
    failures: list[str] = []
    for label, (path, snippet) in REQUIRED_SNIPPETS.items():
        if not path.exists():
            failures.append(f"Missing file for {label}: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if snippet not in text:
            failures.append(f"Missing {snippet!r} in {path}")
    repo_text = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    for table in [
        "restaurant_tables", "restaurant_sessions", "restaurant_order_lines",
        "kitchen_tickets", "restaurant_print_jobs", "restaurant_inventory_consumption",
        "restaurant_orders", "restaurant_split_bills",
    ]:
        if table not in repo_text:
            failures.append(f"Readiness diagnostics do not cover {table}")
    route_text = (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    forbidden_route_sql = ["SELECT ", "INSERT ", "UPDATE ", "DELETE ", ".execute(", ".query("]
    for token in forbidden_route_sql:
        if token in route_text:
            failures.append(f"Restaurant HTTP route still contains forbidden data-access token {token!r}")
    if failures:
        print("Restaurant production readiness guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("Restaurant production readiness guard passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
