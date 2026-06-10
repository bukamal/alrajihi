# -*- coding: utf-8 -*-
import requests
import time
import json
from typing import List, Dict, Any, Tuple
from auth.session import save_token, load_token, clear_token

class RestClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
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


