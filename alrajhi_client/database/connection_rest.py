# -*- coding: utf-8 -*-
import requests
import time
import json
from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Any, Tuple
from auth.session import save_token, load_token, clear_token
try:
    from core.server_control import normalize_server_url
except Exception:
    def normalize_server_url(address=None, port=None, default_scheme="http"):
        raw = str(address or "").strip().rstrip("/")
        if raw.startswith("http//"):
            raw = "http://" + raw[6:]
        if "://" not in raw:
            raw = "http://" + raw
        return raw


REQUEST_LOG = []
MAX_REQUEST_LOG = 120

def _append_request_log(method, endpoint, url, status=None, ok=False, elapsed_ms=None, error=None):
    try:
        REQUEST_LOG.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'method': method,
            'endpoint': endpoint,
            'url': url,
            'status': status,
            'ok': bool(ok),
            'elapsed_ms': elapsed_ms,
            'error': str(error)[:300] if error else '',
        })
        del REQUEST_LOG[:-MAX_REQUEST_LOG]
    except Exception:
        pass

def get_request_log():
    return list(REQUEST_LOG)


def _json_safe(value):
    """Convert Decimal/date/tuple values into JSON-serializable objects for REST payloads."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value

class RestClient:
    def __init__(self, server_url: str):
        self.server_url = normalize_server_url(server_url).rstrip('/')
        self.token = load_token()

    def set_token(self, token: str):
        self.token = token
        save_token(token)

    def _headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def _request(self, method, endpoint, data=None, params=None, retries=3, backoff=1.0, queue_on_failure=True):
        url = f"{self.server_url}{endpoint}"
        last_exception = None
        for attempt in range(retries):
            started = time.perf_counter()
            try:
                resp = requests.request(method, url, json=_json_safe(data), params=_json_safe(params), headers=self._headers(), timeout=10)
                elapsed = int((time.perf_counter() - started) * 1000)
                _append_request_log(method, endpoint, url, status=resp.status_code, ok=resp.status_code < 400, elapsed_ms=elapsed)
                if resp.status_code == 429:
                    wait_time = min(30, backoff * (4 ** attempt))
                    time.sleep(wait_time)
                    continue
                if resp.status_code >= 400:
                    detail = (resp.text or '').strip()
                    # Include the effective URL so remote-mode diagnostics can distinguish
                    # a missing endpoint from a wrong saved server address.
                    raise Exception(f"API error {resp.status_code} at {url}: {detail}")
                return resp.json() if resp.text else None
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                _append_request_log(method, endpoint, url, ok=False, elapsed_ms=int((time.perf_counter() - started) * 1000), error=e)
                last_exception = e
                if attempt == retries - 1 and queue_on_failure:
                    from database.connection import offline_queue
                    if offline_queue.is_queueable(endpoint, method):
                        record_id = None
                        parts = endpoint.split('/')
                        for part in parts:
                            if part.isdigit():
                                record_id = int(part)
                                break
                        qid = offline_queue.add_request(endpoint, method, data, record_id=record_id, error=e)
                        _append_request_log(method, endpoint, url, ok=True, status='QUEUED', error=f'queued #{qid}')
                        return {'queued': True, 'queue_id': qid, 'id': -qid}
                    raise Exception(f"No connection and this operation cannot be queued safely: {endpoint}")
                wait_time = backoff * (2 ** attempt)
                time.sleep(wait_time)
            except Exception as e:
                if not str(e).startswith('API error'):
                    _append_request_log(method, endpoint, url, ok=False, elapsed_ms=int((time.perf_counter() - started) * 1000), error=e)
                last_exception = e
                if attempt < retries - 1:
                    wait_time = backoff * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    raise
        raise last_exception

    # ------------------- المصادقة -------------------
    def login(self, username: str, password: str) -> Dict:
        result = self._request('POST', '/api/login', {'username': username, 'password': password})
        self.set_token(result['token'])
        return result['user']

    def logout(self):
        self._request('POST', '/api/logout', queue_on_failure=False)
        self.token = None
        clear_token()


    def change_password(self, old_password: str, new_password: str):
        return self._request('POST', '/api/users/change_password', {
            'old_password': old_password,
            'new_password': new_password
        }, queue_on_failure=False)

    # ------------------- المستخدمون -------------------
    def get_users(self) -> List[Dict]:
        result = self._request('GET', '/api/users', queue_on_failure=False)
        if isinstance(result, dict):
            return result.get('users', [])
        return result or []

    def add_user(self, data: Dict) -> int:
        result = self._request('POST', '/api/users', data, queue_on_failure=False)
        return result['id']

    def update_user(self, user_id: int, data: Dict):
        return self._request('PUT', f'/api/users/{user_id}', data, queue_on_failure=False)

    def delete_user(self, user_id: int):
        return self._request('DELETE', f'/api/users/{user_id}', queue_on_failure=False)

    # ------------------- الصناديق والبنوك -------------------
    def get_cashboxes(self, include_archived=False) -> List[Dict]:
        params = {'include_archived': 1} if include_archived else {}
        result = self._request('GET', '/api/cashboxes', params=params, queue_on_failure=False)
        return result.get('cashboxes', []) if isinstance(result, dict) else (result or [])

    def get_bank_accounts(self, include_archived=False) -> List[Dict]:
        params = {'include_archived': 1} if include_archived else {}
        result = self._request('GET', '/api/bank_accounts', params=params, queue_on_failure=False)
        return result.get('bank_accounts', []) if isinstance(result, dict) else (result or [])

    def get_cashbox(self, cashbox_id: int) -> Dict:
        return self._request('GET', f'/api/cashboxes/{cashbox_id}', queue_on_failure=False)

    def get_bank_account(self, bank_account_id: int) -> Dict:
        return self._request('GET', f'/api/bank_accounts/{bank_account_id}', queue_on_failure=False)

    def add_cashbox(self, data: Dict) -> int:
        result = self._request('POST', '/api/cashboxes', data, queue_on_failure=False)
        return result['id']

    def update_cashbox(self, cashbox_id: int, data: Dict):
        return self._request('PUT', f'/api/cashboxes/{cashbox_id}', data, queue_on_failure=False)

    def archive_cashbox(self, cashbox_id: int):
        return self._request('DELETE', f'/api/cashboxes/{cashbox_id}', queue_on_failure=False)

    def add_bank_account(self, data: Dict) -> int:
        result = self._request('POST', '/api/bank_accounts', data, queue_on_failure=False)
        return result['id']

    def update_bank_account(self, bank_account_id: int, data: Dict):
        return self._request('PUT', f'/api/bank_accounts/{bank_account_id}', data, queue_on_failure=False)

    def archive_bank_account(self, bank_account_id: int):
        return self._request('DELETE', f'/api/bank_accounts/{bank_account_id}', queue_on_failure=False)

    def get_cash_bank_movements(self, limit=200, cashbox_id=None, bank_account_id=None) -> List[Dict]:
        params = {'limit': limit}
        if cashbox_id: params['cashbox_id'] = cashbox_id
        if bank_account_id: params['bank_account_id'] = bank_account_id
        result = self._request('GET', '/api/cash_bank_movements', params=params, queue_on_failure=False)
        return result.get('movements', []) if isinstance(result, dict) else (result or [])

    def default_cashbox_id(self, branch_id=None):
        params = {}
        if branch_id: params['branch_id'] = branch_id
        result = self._request('GET', '/api/cashboxes/default', params=params, queue_on_failure=False)
        return result.get('id') if isinstance(result, dict) else None


    def add_cash_bank_movement(self, data: Dict) -> int:
        result = self._request('POST', '/api/cash_bank_movements', data, queue_on_failure=True)
        return result.get('id') if isinstance(result, dict) else None

    def delete_reference_movements(self, reference_type, reference_id):
        return self._request('DELETE', '/api/cash_bank_movements/by-reference', params={'reference_type': reference_type, 'reference_id': reference_id}, queue_on_failure=False)

    def current_open_shift(self, cashbox_id=None):
        params = {}
        if cashbox_id: params['cashbox_id'] = cashbox_id
        return self._request('GET', '/api/pos_shifts/current', params=params, queue_on_failure=False)

    def get_shifts(self, limit=100, status=None):
        params = {'limit': limit}
        if status: params['status'] = status
        result = self._request('GET', '/api/pos_shifts', params=params, queue_on_failure=False)
        return result.get('shifts', []) if isinstance(result, dict) else (result or [])

    def open_shift(self, data: Dict) -> int:
        result = self._request('POST', '/api/pos_shifts', data, queue_on_failure=False)
        return result.get('id') if isinstance(result, dict) else None

    def shift_summary(self, shift_id: int):
        return self._request('GET', f'/api/pos_shifts/{shift_id}/summary', queue_on_failure=False)

    def close_shift(self, shift_id: int, actual_amount, notes=''):
        return self._request('POST', f'/api/pos_shifts/{shift_id}/close', {'actual_amount': actual_amount, 'notes': notes}, queue_on_failure=False)


    # ------------------- الفروع والمستودعات -------------------
    def get_branches(self, include_archived=False):
        params = {'include_archived': 1} if include_archived else {}
        result = self._request('GET', '/api/branches', params=params, queue_on_failure=False)
        return result.get('branches', []) if isinstance(result, dict) else (result or [])

    def default_branch_id(self):
        result = self._request('GET', '/api/branches/default', queue_on_failure=False)
        return result.get('id') if isinstance(result, dict) else None

    def get_branch(self, branch_id: int):
        return self._request('GET', f'/api/branches/{branch_id}', queue_on_failure=False)

    def add_branch(self, data: Dict) -> int:
        result = self._request('POST', '/api/branches', data, queue_on_failure=False)
        return result['id']

    def update_branch(self, branch_id: int, data: Dict):
        return self._request('PUT', f'/api/branches/{branch_id}', data, queue_on_failure=False)

    def archive_branch(self, branch_id: int):
        return self._request('DELETE', f'/api/branches/{branch_id}', queue_on_failure=False)

    def get_warehouses(self, include_archived=False):
        params = {'include_archived': 1} if include_archived else {}
        result = self._request('GET', '/api/warehouses', params=params, queue_on_failure=False)
        return result.get('warehouses', []) if isinstance(result, dict) else (result or [])

    def default_warehouse_id(self):
        result = self._request('GET', '/api/warehouses/default', queue_on_failure=False)
        return result.get('id') if isinstance(result, dict) else None

    def get_warehouse(self, warehouse_id: int):
        return self._request('GET', f'/api/warehouses/{warehouse_id}', queue_on_failure=False)

    def add_warehouse(self, data: Dict) -> int:
        result = self._request('POST', '/api/warehouses', data, queue_on_failure=False)
        return result['id']

    def update_warehouse(self, warehouse_id: int, data: Dict):
        return self._request('PUT', f'/api/warehouses/{warehouse_id}', data, queue_on_failure=False)

    def archive_warehouse(self, warehouse_id: int):
        return self._request('DELETE', f'/api/warehouses/{warehouse_id}', queue_on_failure=False)

    def warehouse_available_qty(self, item_id: int, warehouse_id=None):
        params = {'item_id': item_id}
        if warehouse_id: params['warehouse_id'] = warehouse_id
        result = self._request('GET', '/api/warehouses/available_qty', params=params, queue_on_failure=False)
        return result.get('quantity', '0') if isinstance(result, dict) else '0'

    def warehouse_record_movement(self, data: Dict) -> int:
        result = self._request('POST', '/api/warehouses/movements', data, queue_on_failure=False)
        return int(result.get('id') or 0) if isinstance(result, dict) else 0

    def warehouse_reverse_reference(self, reference_type, reference_id):
        return self._request('POST', '/api/warehouses/reverse_reference', {
            'reference_type': reference_type,
            'reference_id': reference_id,
        }, queue_on_failure=False)

    def get_warehouse_balances(self, search=None, warehouse_id=None, limit=None, offset=None):
        params = {}
        if search: params['search'] = search
        if warehouse_id: params['warehouse_id'] = warehouse_id
        if limit is not None: params['limit'] = limit
        if offset is not None: params['offset'] = offset
        result = self._request('GET', '/api/warehouses/balances', params=params, queue_on_failure=False)
        return result.get('balances', []) if isinstance(result, dict) else (result or [])

    def get_warehouse_balance_count(self, search=None, warehouse_id=None):
        params = {}
        if search: params['search'] = search
        if warehouse_id: params['warehouse_id'] = warehouse_id
        result = self._request('GET', '/api/warehouses/balances/count', params=params, queue_on_failure=False)
        return int(result.get('count') or 0) if isinstance(result, dict) else 0

    def get_warehouse_movements(self, item_id=None, warehouse_id=None, limit=100):
        params = {'limit': limit}
        if item_id: params['item_id'] = item_id
        if warehouse_id: params['warehouse_id'] = warehouse_id
        result = self._request('GET', '/api/warehouses/movements', params=params, queue_on_failure=False)
        return result.get('movements', []) if isinstance(result, dict) else (result or [])

    def create_warehouse_transfer(self, data: Dict) -> int:
        result = self._request('POST', '/api/warehouses/transfers', data, queue_on_failure=False)
        return int(result.get('id') or 0) if isinstance(result, dict) else 0

    def cancel_warehouse_transfer(self, transfer_id: int):
        return self._request('POST', f'/api/warehouses/transfers/{transfer_id}/cancel', queue_on_failure=False)

    def get_warehouse_transfers(self, limit=200):
        result = self._request('GET', '/api/warehouses/transfers', params={'limit': limit}, queue_on_failure=False)
        return result.get('transfers', []) if isinstance(result, dict) else (result or [])

    def get_categories(self, search=None, include_inactive=False, include_deleted=False):
        params = {}
        if search: params['search'] = search
        if include_inactive: params['include_inactive'] = 1
        if include_deleted: params['include_deleted'] = 1
        result = self._request('GET', '/api/categories', params=params)
        return result.get('categories', []) if isinstance(result, dict) else (result or [])

    def add_category(self, data: Dict) -> int:
        result = self._request('POST', '/api/categories', data)
        return result['id']

    def update_category(self, category_id: int, data: Dict):
        self._request('PUT', f'/api/categories/{category_id}', data)

    def delete_category(self, category_id: int):
        self._request('DELETE', f'/api/categories/{category_id}')

    def restore_category(self, category_id: int):
        self._request('POST', f'/api/categories/{category_id}/restore')

    # ------------------- المواد -------------------
    def get_items(self, search=None, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if search: params['search'] = search
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/items', params=params)
        return result.get('items', []), result.get('total', 0)

    def get_item(self, item_id: int) -> Dict:
        return self._request('GET', f'/api/items/{item_id}', queue_on_failure=False)

    def add_item(self, data: Dict) -> int:
        result = self._request('POST', '/api/items', data)
        return result['id']

    def update_item(self, item_id: int, data: Dict):
        self._request('PUT', f'/api/items/{item_id}', data)

    def delete_item(self, item_id: int):
        self._request('DELETE', f'/api/items/{item_id}')

    # ------------------- العملاء -------------------
    def get_customers(self, search=None, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if search: params['search'] = search
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/customers', params=params)
        return result.get('customers', []), result.get('total', 0)

    def add_customer(self, data: Dict) -> int:
        result = self._request('POST', '/api/customers', data)
        return result['id']

    def update_customer(self, customer_id: int, data: Dict):
        self._request('PUT', f'/api/customers/{customer_id}', data)

    def delete_customer(self, customer_id: int):
        self._request('DELETE', f'/api/customers/{customer_id}')

    # ------------------- الموردين -------------------
    def get_suppliers(self, search=None, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if search: params['search'] = search
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/suppliers', params=params)
        return result.get('suppliers', []), result.get('total', 0)

    def add_supplier(self, data: Dict) -> int:
        result = self._request('POST', '/api/suppliers', data)
        return result['id']

    def update_supplier(self, supplier_id: int, data: Dict):
        self._request('PUT', f'/api/suppliers/{supplier_id}', data)

    def delete_supplier(self, supplier_id: int):
        self._request('DELETE', f'/api/suppliers/{supplier_id}')

    # ------------------- الفواتير -------------------
    def get_invoices(self, inv_type=None, start_date=None, end_date=None, limit=None, offset=None,
                     search=None, customer_id=None, supplier_id=None) -> Tuple[List[Dict], int]:
        params = {}
        if inv_type: params['type'] = inv_type
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        if search: params['search'] = search
        if customer_id: params['customer_id'] = customer_id
        if supplier_id: params['supplier_id'] = supplier_id
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/invoices', params=params)
        return result.get('invoices', []), result.get('total', 0)

    def get_invoice_by_id(self, invoice_id: int) -> Dict:
        return self._request('GET', f'/api/invoices/{invoice_id}')

    def add_invoice(self, data: Dict) -> int:
        result = self._request('POST', '/api/invoices', data)
        return result['id']

    def update_invoice(self, invoice_id: int, data: Dict):
        self._request('PUT', f'/api/invoices/{invoice_id}', data)

    def delete_invoice(self, invoice_id: int):
        self._request('DELETE', f'/api/invoices/{invoice_id}')

    def transition_invoice_workflow(self, invoice_id: int, status: str, action: str = None, notes: str = '') -> Dict:
        payload = {'status': status, 'action': action or str(status).lower(), 'notes': notes or ''}
        return self._request('POST', f'/api/invoices/{invoice_id}/workflow', payload, queue_on_failure=False)


    def get_next_invoice_reference(self, inv_type: str) -> str:
        result = self._request('GET', '/api/invoices/next-reference', params={'type': inv_type}, queue_on_failure=False)
        return result.get('reference') if isinstance(result, dict) else str(result)

    # ------------------- التصنيع -------------------
    def get_boms(self, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/manufacturing/boms', params=params)
        return result.get('boms', []), result.get('total', 0)

    def get_bom(self, bom_id: int) -> Dict:
        return self._request('GET', f'/api/manufacturing/boms/{bom_id}')

    def save_bom(self, data: Dict) -> int:
        result = self._request('POST', '/api/manufacturing/boms', data)
        return result['id']

    def delete_bom(self, bom_id: int):
        self._request('DELETE', f'/api/manufacturing/boms/{bom_id}')

    def get_production_orders(self, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/manufacturing/orders', params=params)
        return result.get('orders', []), result.get('total', 0)

    def get_production_order(self, order_id: int) -> Dict:
        return self._request('GET', f'/api/manufacturing/orders/{order_id}')

    def create_production_order(self, data: Dict) -> int:
        result = self._request('POST', '/api/manufacturing/orders', data)
        return result['id']

    def start_production(self, order_id: int):
        self._request('POST', f'/api/manufacturing/orders/{order_id}/start')

    def complete_production(self, order_id: int, produced_qty: float):
        self._request('POST', f'/api/manufacturing/orders/{order_id}/complete', {'produced_qty': produced_qty})

    def consume_material(self, order_id: int, item_id: int, consumed_qty: float, unit_cost: float):
        self._request('POST', f'/api/manufacturing/orders/{order_id}/consume', {'item_id': item_id, 'consumed_qty': consumed_qty, 'unit_cost': unit_cost})

    def delete_production_order(self, order_id: int):
        self._request('DELETE', f'/api/manufacturing/orders/{order_id}')

    def reverse_production_order(self, order_id: int):
        self._request('POST', f'/api/manufacturing/orders/{order_id}/reverse')


    # ------------------- تصنيع: وظائف تفصيلية -------------------
    def get_bom_for_product(self, product_id: int):
        return self._request('GET', f'/api/manufacturing/boms/by-product/{product_id}', queue_on_failure=False)

    def can_edit_bom(self, bom_id: int):
        result = self._request('GET', f'/api/manufacturing/boms/{bom_id}/can-edit', queue_on_failure=False)
        return bool(result.get('can_edit', False)), result.get('message', '')

    def cancel_production(self, order_id: int):
        return self._request('POST', f'/api/manufacturing/orders/{order_id}/cancel', queue_on_failure=False)

    def get_reservations(self, order_id: int):
        result = self._request('GET', f'/api/manufacturing/orders/{order_id}/reservations', queue_on_failure=False)
        return result.get('reservations', []) if isinstance(result, dict) else (result or [])

    def get_consumptions(self, order_id: int):
        result = self._request('GET', f'/api/manufacturing/orders/{order_id}/consumptions', queue_on_failure=False)
        return result.get('consumptions', []) if isinstance(result, dict) else (result or [])

    def get_outputs(self, order_id: int):
        result = self._request('GET', f'/api/manufacturing/orders/{order_id}/outputs', queue_on_failure=False)
        return result.get('outputs', []) if isinstance(result, dict) else (result or [])

    def get_required_materials(self, bom_id: int, planned_qty):
        result = self._request('GET', f'/api/manufacturing/boms/{bom_id}/required-materials', params={'planned_qty': planned_qty}, queue_on_failure=False)
        return result.get('materials', []) if isinstance(result, dict) else (result or [])

    def check_materials_availability(self, bom_id: int, planned_qty):
        result = self._request('GET', f'/api/manufacturing/boms/{bom_id}/availability', params={'planned_qty': planned_qty}, queue_on_failure=False)
        return bool(result.get('sufficient', False)), result.get('materials', [])

    def delete_consumption(self, consumption_id: int):
        return self._request('DELETE', f'/api/manufacturing/consumptions/{consumption_id}', queue_on_failure=False)

    def delete_output(self, output_id: int):
        return self._request('DELETE', f'/api/manufacturing/outputs/{output_id}', queue_on_failure=False)

    def cancel_production_order(self, order_id: int):
        return self.cancel_production(order_id)

    # ------------------- السندات -------------------
    def get_vouchers(self, vtype=None, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if vtype: params['type'] = vtype
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/vouchers', params=params)
        return result.get('vouchers', []), result.get('total', 0)

    def get_voucher(self, voucher_id: int) -> Dict:
        return self._request('GET', f'/api/vouchers/{voucher_id}')

    def add_voucher(self, data: Dict) -> int:
        result = self._request('POST', '/api/vouchers', data)
        return result['id']

    def update_voucher(self, voucher_id: int, data: Dict):
        self._request('PUT', f'/api/vouchers/{voucher_id}', data)

    def delete_voucher(self, voucher_id: int):
        self._request('DELETE', f'/api/vouchers/{voucher_id}')

    # ------------------- المصروفات (متوافقة مع السندات) -------------------
    def get_expenses(self, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if limit: params['limit'] = limit
        if offset: params['offset'] = offset
        result = self._request('GET', '/api/expenses', params=params)
        return result.get('expenses', []), result.get('total', 0)

    def add_expense(self, data: Dict) -> int:
        result = self._request('POST', '/api/expenses', data)
        return result['id']

    def update_expense(self, expense_id: int, data: Dict):
        self._request('PUT', f'/api/expenses/{expense_id}', data)

    def delete_expense(self, expense_id: int):
        self._request('DELETE', f'/api/expenses/{expense_id}')

    # ------------------- التقارير -------------------
    def get_summary(self, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', '/api/reports/summary', params=params)

    def get_income_statement(self, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', '/api/reports/income_statement', params=params)

    def get_balance_sheet(self, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', '/api/reports/balance_sheet', params=params)

    def get_customer_statement(self, customer_id: int, start_date=None, end_date=None) -> List[Dict]:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        result = self._request('GET', f'/api/reports/customers/{customer_id}/statement', params=params)
        return result.get('rows', result if isinstance(result, list) else [])

    def get_supplier_statement(self, supplier_id: int, start_date=None, end_date=None) -> List[Dict]:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        result = self._request('GET', f'/api/reports/suppliers/{supplier_id}/statement', params=params)
        return result.get('rows', result if isinstance(result, list) else [])

    def get_customer_balances(self) -> List[Dict]:
        result = self._request('GET', '/api/reports/customers/balances')
        return result.get('rows', result if isinstance(result, list) else [])

    def get_supplier_balances(self) -> List[Dict]:
        result = self._request('GET', '/api/reports/suppliers/balances')
        return result.get('rows', result if isinstance(result, list) else [])

    def get_customer_aging(self, as_of_date=None) -> List[Dict]:
        params = {}
        if as_of_date: params['as_of_date'] = as_of_date
        result = self._request('GET', '/api/reports/customers/aging', params=params)
        return result.get('rows', result if isinstance(result, list) else [])

    def get_supplier_aging(self, as_of_date=None) -> List[Dict]:
        params = {}
        if as_of_date: params['as_of_date'] = as_of_date
        result = self._request('GET', '/api/reports/suppliers/aging', params=params)
        return result.get('rows', result if isinstance(result, list) else [])

    def get_trial_balance(self) -> List[Dict]:
        result = self._request('GET', '/api/reports/trial_balance')
        return result.get('rows', result if isinstance(result, list) else [])

    def get_accounting_trial_balance(self) -> List[Dict]:
        result = self._request('GET', '/api/reports/accounting/trial_balance')
        return result.get('rows', result if isinstance(result, list) else [])

    def get_accounting_ledger(self, account_id=None, start_date=None, end_date=None, limit=1000) -> List[Dict]:
        params = {'limit': limit}
        if account_id: params['account_id'] = account_id
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        result = self._request('GET', '/api/reports/accounting/ledger', params=params)
        return result.get('rows', result if isinstance(result, list) else [])

    def get_accounting_income_statement(self, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', '/api/reports/accounting/income_statement', params=params)

    def get_accounting_balance_sheet(self, as_of_date=None) -> Dict:
        params = {}
        if as_of_date: params['as_of_date'] = as_of_date
        return self._request('GET', '/api/reports/accounting/balance_sheet', params=params)

    def get_accounting_cash_flow(self, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', '/api/reports/accounting/cash_flow', params=params)


    def get_accounting_receivables_aging(self, as_of_date=None) -> Dict:
        params = {}
        if as_of_date: params['as_of_date'] = as_of_date
        return self._request('GET', '/api/reports/accounting/receivables/aging', params=params)

    def get_accounting_payables_aging(self, as_of_date=None) -> Dict:
        params = {}
        if as_of_date: params['as_of_date'] = as_of_date
        return self._request('GET', '/api/reports/accounting/payables/aging', params=params)

    def get_accounting_customer_statement(self, customer_id, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', f'/api/reports/accounting/customers/{customer_id}/statement', params=params)

    def get_accounting_supplier_statement(self, supplier_id, start_date=None, end_date=None) -> Dict:
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
        return self._request('GET', f'/api/reports/accounting/suppliers/{supplier_id}/statement', params=params)


    # ------------------- Phase157 RBAC -------------------
    def get_rbac_roles(self) -> List[Dict]:
        return self._request('GET', '/api/rbac/roles')

    def get_rbac_permissions(self) -> List[Dict]:
        return self._request('GET', '/api/rbac/permissions')

    def get_my_permissions(self) -> Dict:
        return self._request('GET', '/api/rbac/me')

    def set_user_roles(self, user_id: str, roles: List[str]) -> Dict:
        return self._request('PUT', f'/api/rbac/users/{user_id}/roles', {'roles': roles})

    def set_role_permissions(self, role_name: str, permissions: List[str]) -> Dict:
        return self._request('PUT', f'/api/rbac/roles/{role_name}/permissions', {'permissions': permissions})

    def set_user_branch_access(self, user_id: str, branch_ids: List[int]) -> Dict:
        return self._request('PUT', f'/api/rbac/users/{user_id}/branches', {'branch_ids': branch_ids})

    # ------------------- الإعدادات -------------------
    def get_setting(self, key: str) -> Any:
        result = self._request('GET', f'/api/settings/{key}')
        return result.get('value')

    def set_setting(self, key: str, value: str):
        self._request('POST', f'/api/settings/{key}', {'value': value})

    def get_all_currencies(self) -> List[Dict]:
        return self._request('GET', '/api/exchange_rates')

    def update_exchange_rate(self, currency_code: str, rate_to_usd: float):
        self._request('PUT', f'/api/exchange_rates/{currency_code}', {'rate_to_usd': rate_to_usd})

    def get_historical_rate(self, currency_code: str, date: str) -> float:
        result = self._request('GET', f'/api/exchange_rates/{currency_code}/history', params={'date': date})
        return result.get('rate_to_usd', 1.0) if result else 1.0

    # ------------------- المرتجعات -------------------
    def get_sales_returns(self, search=None, limit=None, offset=None):
        params = {}
        if search: params['search'] = search
        if limit is not None: params['limit'] = limit
        if offset is not None: params['offset'] = offset
        result = self._request('GET', '/api/returns/sales', params=params, queue_on_failure=False)
        return result.get('returns', []), result.get('total', 0)

    def get_purchase_returns(self, search=None, limit=None, offset=None):
        params = {}
        if search: params['search'] = search
        if limit is not None: params['limit'] = limit
        if offset is not None: params['offset'] = offset
        result = self._request('GET', '/api/returns/purchase', params=params, queue_on_failure=False)
        return result.get('returns', []), result.get('total', 0)

    def get_sales_return(self, return_id: int):
        return self._request('GET', f'/api/returns/sales/{return_id}', queue_on_failure=False)

    def get_purchase_return(self, return_id: int):
        return self._request('GET', f'/api/returns/purchase/{return_id}', queue_on_failure=False)

    def get_sales_return_invoices(self, search=None, limit=200):
        params = {'limit': limit}
        if search: params['search'] = search
        result = self._request('GET', '/api/returns/sales/invoices', params=params, queue_on_failure=False)
        return result.get('invoices', [])

    def get_purchase_return_invoices(self, search=None, limit=200):
        params = {'limit': limit}
        if search: params['search'] = search
        result = self._request('GET', '/api/returns/purchase/invoices', params=params, queue_on_failure=False)
        return result.get('invoices', [])

    def get_sales_returnable_lines(self, invoice_id: int):
        result = self._request('GET', f'/api/returns/sales/invoices/{invoice_id}/lines', queue_on_failure=False)
        return result.get('lines', [])

    def get_purchase_returnable_lines(self, invoice_id: int):
        result = self._request('GET', f'/api/returns/purchase/invoices/{invoice_id}/lines', queue_on_failure=False)
        return result.get('lines', [])

    def create_sales_return(self, data: Dict[str, Any]):
        return self._request('POST', '/api/returns/sales', data=data, queue_on_failure=True)

    def create_purchase_return(self, data: Dict[str, Any]):
        return self._request('POST', '/api/returns/purchase', data=data, queue_on_failure=True)

    def delete_sales_return(self, return_id: int):
        return self._request('DELETE', f'/api/returns/sales/{return_id}', queue_on_failure=True)

    def delete_purchase_return(self, return_id: int):
        return self._request('DELETE', f'/api/returns/purchase/{return_id}', queue_on_failure=True)

    # ------------------- سجل التدقيق -------------------
    def get_audit_log(self, limit: int = 2000, offset: int = 0) -> List[Dict]:
        params = {'limit': limit, 'offset': offset}
        result = self._request('GET', '/api/audit_log', params=params, queue_on_failure=False)
        if isinstance(result, dict):
            return result.get('logs', [])
        return result or []

    def delete_old_audit_logs(self, days: int = 90):
        return self._request('DELETE', '/api/audit_log/old', data={'days': days}, queue_on_failure=False)


    # ------------------- تشخيص وضع الشبكة -------------------


    # ------------------- مراقبة التشغيل -------------------
    def get_monitoring_health(self, tolerance='0') -> Dict:
        return self._request('GET', '/api/monitoring/health', params={'tolerance': tolerance}, queue_on_failure=False)

    def debug_status(self) -> Dict:
        return self._request('GET', '/api/debug/status', queue_on_failure=False)


    # ------------------- inventory / ledger -------------------
    def get_inventory_movements(self, item_id: int) -> List[Dict]:
        result = self._request('GET', f'/api/items/{item_id}/inventory-movements', queue_on_failure=False)
        return result.get('movements', []) if isinstance(result, dict) else (result or [])

    def record_inventory_movement(self, data: Dict) -> int:
        result = self._request('POST', '/api/inventory-movements', data)
        return result.get('id') if isinstance(result, dict) else result

    def get_inventory_ledger(self, **filters) -> List[Dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        result = self._request('GET', '/api/inventory-ledger', params=params, queue_on_failure=False)
        return result.get('ledger', []) if isinstance(result, dict) else (result or [])

    def record_inventory_ledger_entry(self, data: Dict) -> int:
        result = self._request('POST', '/api/inventory-ledger', data)
        return result.get('id') if isinstance(result, dict) else result

    def get_inventory_ledger_balance(self, item_id: int, warehouse_id=None):
        params = {'item_id': item_id}
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        result = self._request('GET', '/api/inventory-ledger/balance', params=params, queue_on_failure=False)
        return result.get('balance', '0') if isinstance(result, dict) else result

    def get_inventory_ledger_reconciliation(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict:
        params = {'tolerance': tolerance}
        if item_id is not None:
            params['item_id'] = item_id
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        return self._request('GET', '/api/inventory-ledger/reconciliation', params=params, queue_on_failure=False) or {}

    def get_inventory_ledger_snapshot(self, item_id=None, warehouse_id=None) -> Dict:
        params = {}
        if item_id is not None:
            params['item_id'] = item_id
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        return self._request('GET', '/api/inventory-ledger/snapshot', params=params, queue_on_failure=False) or {}

    def get_inventory_ledger_health(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict:
        params = {'tolerance': tolerance}
        if item_id is not None:
            params['item_id'] = item_id
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        return self._request('GET', '/api/inventory-ledger/health', params=params, queue_on_failure=False) or {}

    def get_inventory_ledger_dual_read(self, item_id=None, warehouse_id=None, tolerance='0', include_matches=True) -> Dict:
        params = {'tolerance': tolerance, 'include_matches': 1 if include_matches else 0}
        if item_id is not None:
            params['item_id'] = item_id
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        return self._request('GET', '/api/inventory-ledger/dual-read', params=params, queue_on_failure=False) or {}

    def get_inventory_ledger_readiness(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict:
        params = {'tolerance': tolerance}
        if item_id is not None:
            params['item_id'] = item_id
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        return self._request('GET', '/api/inventory-ledger/readiness', params=params, queue_on_failure=False) or {}

    def get_inventory_ledger_controlled_read(self, item_id=None, warehouse_id=None, mode='operational', tolerance='0') -> Dict:
        params = {'mode': mode or 'operational', 'tolerance': tolerance}
        if item_id is not None:
            params['item_id'] = item_id
        if warehouse_id is not None:
            params['warehouse_id'] = warehouse_id
        return self._request('GET', '/api/inventory-ledger/controlled-read', params=params, queue_on_failure=False) or {}

    def inventory_ledger_backfill(self, dry_run=True, item_id=None, warehouse_id=None, clear_existing=False, include_item_movements=True, include_warehouse_movements=True) -> Dict:
        payload = {
            'dry_run': bool(dry_run),
            'clear_existing': bool(clear_existing),
            'include_item_movements': bool(include_item_movements),
            'include_warehouse_movements': bool(include_warehouse_movements),
        }
        if item_id is not None:
            payload['item_id'] = item_id
        if warehouse_id is not None:
            payload['warehouse_id'] = warehouse_id
        return self._request('POST', '/api/inventory-ledger/backfill', payload, queue_on_failure=False) or {}
