from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_restaurant_gateway_exposes_menu_items_boundary():
    gateway = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    assert 'def list_menu_items(' in gateway
    assert 'SELECT id, name, category_id, selling_price, unit, barcode, quantity' in local
    assert '/api/restaurant/menu_items' in remote
    assert 'def list_menu_items(' in service


def test_restaurant_pos_has_product_card_grid_and_manual_fallback():
    pos = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_pos_widget.py').read_text(encoding='utf-8')
    assert 'QScrollArea' in pos
    assert 'restaurantMenuItemButton' in pos
    assert 'def add_menu_item' in pos
    assert 'restaurant.manual_item' in pos
    assert 'self.service.list_menu_items' in pos
    assert 'item_id=item.get("id")' in pos


def test_restaurant_server_menu_endpoint_is_repository_backed():
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    repo = (ROOT / 'alrajhi_server' / 'repositories' / 'restaurant_repository.py').read_text(encoding='utf-8')
    assert '@restaurant_bp.route("/restaurant/menu_items", methods=["GET"])' in routes
    assert '_repo.list_menu_items' in routes
    assert 'def list_menu_items(' in repo


def test_phase25_translations_and_qss_exist():
    translator = (ROOT / 'alrajhi_client' / 'i18n' / 'translator.py').read_text(encoding='utf-8')
    qss = (ROOT / 'alrajhi_client' / 'theme' / 'qss.py').read_text(encoding='utf-8')
    assert "'restaurant.search_menu': 'ابحث في قائمة المطعم...'" in translator
    assert "'restaurant.search_menu': 'Restaurantkarte durchsuchen...'" in translator
    assert "'restaurant.search_menu': 'Search restaurant menu...'" in translator
    assert 'Phase 25: product-card ordering grid' in qss
    assert 'QPushButton#restaurantMenuItemButton' in qss
