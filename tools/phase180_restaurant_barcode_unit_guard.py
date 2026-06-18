# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    service = read('alrajhi_client/core/services/restaurant_service.py')
    widget = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
    gateway = read('alrajhi_client/gateways/local/restaurant_gateway.py')
    remote = read('alrajhi_client/gateways/remote/restaurant_gateway.py')
    server_repo = read('alrajhi_server/repositories/restaurant_repository.py')
    server_route = read('alrajhi_server/services/http_routes/restaurant.py')
    tr = read('alrajhi_client/i18n/translator.py')

    require('barcode_input_service' in service, 'RestaurantService must use barcode_input_service')
    require('def add_entry' in service, 'RestaurantService.add_entry is required')
    require('matched_unit' in service and 'conversion_factor' in service and 'base_qty' in service, 'RestaurantService must preserve unit barcode metadata')
    require('handle_entry_return' in widget, 'RestaurantPOSWidget must route scanner Return through barcode handler')
    require('lookup_entry' not in widget, 'Widget must not bypass RestaurantService.add_entry with raw lookup_entry')
    require('add_entry' in widget, 'RestaurantPOSWidget must call RestaurantService.add_entry for scan-like input')
    for token in ('unit_id', 'unit', 'conversion_factor', 'base_qty', 'barcode_scope', 'matched_barcode'):
        require(token in gateway, f'LocalRestaurantGateway missing {token}')
        require(token in remote, f'RemoteRestaurantGateway missing {token}')
        require(token in server_repo, f'Server restaurant repository missing {token}')
        require(token in server_route, f'Server restaurant route missing {token}')
    require('restaurant.search_menu_or_barcode' in tr, 'Missing restaurant barcode search translation')
    require('restaurant.unit_barcode_scope' in tr, 'Missing restaurant unit barcode translation')
    print('phase180_restaurant_barcode_unit_guard passed')


if __name__ == '__main__':
    main()
