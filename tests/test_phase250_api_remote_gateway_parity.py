from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def test_phase250_remote_return_gateways_are_concrete_and_delegate_update():
    from gateways.remote.sales_return_gateway import RemoteSalesReturnGateway
    from gateways.remote.purchase_return_gateway import RemotePurchaseReturnGateway

    class DummyRestClient:
        def __init__(self):
            self.calls = []

        def update_sales_return(self, return_id, data):
            self.calls.append(('sales', return_id, data))
            return {'id': return_id + 10}

        def update_purchase_return(self, return_id, data):
            self.calls.append(('purchase', return_id, data))
            return {'id': return_id + 20}

    rc = DummyRestClient()
    sales = RemoteSalesReturnGateway(rc)
    purchase = RemotePurchaseReturnGateway(rc)

    assert sales.update_return(7, {'notes': 'network update'}) == 17
    assert purchase.update_return(8, {'notes': 'network update'}) == 28
    assert rc.calls == [
        ('sales', 7, {'notes': 'network update'}),
        ('purchase', 8, {'notes': 'network update'}),
    ]


def test_phase250_rest_client_exposes_put_update_methods():
    text = (ROOT / 'alrajhi_client/database/connection_rest.py').read_text(encoding='utf-8')
    assert 'def update_sales_return' in text
    assert "'PUT', f'/api/returns/sales/{return_id}'" in text
    assert 'def update_purchase_return' in text
    assert "'PUT', f'/api/returns/purchase/{return_id}'" in text
    assert 'queue_on_failure=True' in text


def test_phase250_server_exposes_return_put_routes_and_user_scope():
    text = (ROOT / 'alrajhi_server/repositories/http_route_sql/returns.py').read_text(encoding='utf-8')
    assert "@returns_bp.route('/returns/sales/<int:return_id>', methods=['PUT'])" in text
    assert "@returns_bp.route('/returns/purchase/<int:return_id>', methods=['PUT'])" in text
    assert 'def update_sales_return(return_id):' in text
    assert 'def update_purchase_return(return_id):' in text
    assert 'get_jwt_identity()' in text
    assert 'WHERE id=? AND user_id=?' in text
    assert "data.setdefault('return_no', old.get('return_no'))" in text
    assert "data.setdefault('original_invoice_id', old.get('original_invoice_id'))" in text


def test_phase250_local_remote_shortcuts_use_server_put_contract():
    sales = (ROOT / 'alrajhi_client/gateways/local/sales_return_gateway.py').read_text(encoding='utf-8')
    purchase = (ROOT / 'alrajhi_client/gateways/local/purchase_return_gateway.py').read_text(encoding='utf-8')
    assert '.update_sales_return(return_id, data or {})' in sales
    assert '.update_purchase_return(return_id, data or {})' in purchase
    assert 'self.delete_return(return_id)\n            return self.create_return(data)' not in sales
    assert 'self.delete_return(return_id)\n            return self.create_return(data)' not in purchase


def test_phase250_phase_document_exists():
    doc = ROOT / 'PHASE250_API_REMOTE_GATEWAY_PARITY.md'
    assert doc.exists()
    text = doc.read_text(encoding='utf-8')
    assert 'PUT /api/returns/sales/<id>' in text
    assert 'PUT /api/returns/purchase/<id>' in text
