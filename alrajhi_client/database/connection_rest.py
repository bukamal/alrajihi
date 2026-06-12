# -*- coding: utf-8 -*-
import requests
import time
import json
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
            try:
                resp = requests.request(method, url, json=data, params=params, headers=self._headers(), timeout=10)
                if resp.status_code == 429:
                    wait_time = min(30, backoff * (4 ** attempt))
                    time.sleep(wait_time)
                    continue
                if resp.status_code >= 400:
                    raise Exception(f"API error {resp.status_code}: {resp.text}")
                return resp.json() if resp.text else None
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt == retries - 1 and queue_on_failure:
                    # استخراج record_id من endpoint (للطلبات التي تحتوي على معرف في المسار)
                    record_id = None
                    parts = endpoint.split('/')
                    for part in parts:
                        if part.isdigit():
                            record_id = int(part)
                            break
                    from database.connection import offline_queue
                    offline_queue.add_request(endpoint, method, data, record_id=record_id)
                    raise Exception(f"Request queued due to no connection: {endpoint}")
                wait_time = backoff * (2 ** attempt)
                time.sleep(wait_time)
            except Exception as e:
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
    def get_invoices(self, inv_type=None, start_date=None, end_date=None, limit=None, offset=None) -> Tuple[List[Dict], int]:
        params = {}
        if inv_type: params['type'] = inv_type
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
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

