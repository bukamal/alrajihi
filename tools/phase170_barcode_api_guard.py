# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 170 checks for exact barcode lookup across local/remote/API layers."""

import ast
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REMOTE_GATEWAY = ROOT / "alrajhi_client" / "gateways" / "remote" / "product_gateway.py"
REST_CLIENT = ROOT / "alrajhi_client" / "database" / "connection_rest.py"
SERVER_ITEMS = ROOT / "alrajhi_server" / "repositories" / "http_route_sql" / "items.py"
LOCAL_CONNECTION = ROOT / "alrajhi_client" / "database" / "connection.py"
ITEM_DAO = ROOT / "alrajhi_client" / "database" / "dao" / "item_dao.py"
SERVER_CONTROL = ROOT / "alrajhi_client" / "core" / "server_control.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_source(path: Path, function_name: str) -> str:
    text = _source(path)
    tree = ast.parse(text, filename=str(path))
    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return "\n".join(lines[node.lineno - 1: node.end_lineno])
    return ""


def check_remote_gateway(errors: list[str]) -> None:
    src = _function_source(REMOTE_GATEWAY, "get_by_barcode")
    if not src:
        errors.append(f"{REMOTE_GATEWAY}: RemoteItemGateway.get_by_barcode missing")
        return
    if "get_item_by_barcode" not in src:
        errors.append(f"{REMOTE_GATEWAY}: remote barcode lookup must call REST exact endpoint")
    tree = ast.parse(textwrap.dedent(src))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "list":
            has_search = any(kw.arg == "search" for kw in node.keywords)
            has_limit = any(kw.arg == "limit" for kw in node.keywords)
            if not (has_search and has_limit):
                errors.append(f"{REMOTE_GATEWAY}: remote barcode lookup must not download the full catalog")
    if "exact =" not in src:
        errors.append(f"{REMOTE_GATEWAY}: fallback must preserve exact-match semantics")


def check_rest_client(errors: list[str]) -> None:
    src = _source(REST_CLIENT)
    if "def get_item_by_barcode" not in src:
        errors.append(f"{REST_CLIENT}: RestClient.get_item_by_barcode missing")
    if "'/api/items/by-barcode'" not in src:
        errors.append(f"{REST_CLIENT}: exact barcode endpoint is not used")
    if "queue_on_failure=False" not in _function_source(REST_CLIENT, "get_item_by_barcode"):
        errors.append(f"{REST_CLIENT}: barcode lookup must be read-only and not queued")


def check_server_endpoint(errors: list[str]) -> None:
    src = _source(SERVER_ITEMS)
    required = [
        "@items_bp.route('/items/by-barcode'",
        "def get_item_by_barcode",
        "AND i.barcode=?",
        "LIMIT 1",
        "_attach_units",
    ]
    for marker in required:
        if marker not in src:
            errors.append(f"{SERVER_ITEMS}: missing exact barcode API marker {marker!r}")
    if "LIKE" in _function_source(SERVER_ITEMS, "get_item_by_barcode"):
        errors.append(f"{SERVER_ITEMS}: exact barcode API must not use LIKE/fuzzy search")


def check_local_exact_lookup(errors: list[str]) -> None:
    src = _source(LOCAL_CONNECTION)
    if "def get_item_by_barcode" not in src:
        errors.append(f"{LOCAL_CONNECTION}: local exact get_item_by_barcode missing")
    local_fn = _function_source(LOCAL_CONNECTION, "get_item_by_barcode")
    if "AND i.barcode=?" not in local_fn or "LIMIT 1" not in local_fn:
        errors.append(f"{LOCAL_CONNECTION}: local barcode lookup must be exact and bounded")
    dao = _function_source(ITEM_DAO, "get_by_barcode")
    if "records(self.get_items())" in dao:
        errors.append(f"{ITEM_DAO}: ItemDAO.get_by_barcode must not load the full catalog")


def check_remote_route_contract(errors: list[str]) -> None:
    src = _source(SERVER_CONTROL)
    if "'/api/items/by-barcode'" not in src:
        errors.append(f"{SERVER_CONTROL}: remote route contract must include /api/items/by-barcode")


def main() -> None:
    errors: list[str] = []
    check_remote_gateway(errors)
    check_rest_client(errors)
    check_server_endpoint(errors)
    check_local_exact_lookup(errors)
    check_remote_route_contract(errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print("phase170_barcode_api_guard passed")


if __name__ == "__main__":
    main()
