# -*- coding: utf-8 -*-
"""Reporting service facade for dashboard and reports UI.

This service centralizes report access and keeps widgets independent from the
legacy reporting DAO contract.  The DAO/repository layer remains in place for
backward compatibility; UI code should prefer this service.
"""
from __future__ import annotations

from typing import Dict, List

from gateways.reporting_gateway import create_reporting_gateway


class ReportingService:
    """Read-only reporting facade over the active reporting gateway."""

    def __init__(self):
        self._gateway = create_reporting_gateway()

    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.summary(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.income_statement(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.balance_sheet(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def customer_statement(self, customer_id: int) -> List[Dict]:
        result = self._gateway.customer_statement(customer_id)
        return result if isinstance(result, list) else []

    def supplier_statement(self, supplier_id: int) -> List[Dict]:
        result = self._gateway.supplier_statement(supplier_id)
        return result if isinstance(result, list) else []

    def trial_balance(self) -> List[Dict]:
        result = self._gateway.trial_balance()
        return result if isinstance(result, list) else []


    # ========== Warehouse reports ==========
    def warehouse_balances(self, warehouse_id: int | None = None, search: str | None = None) -> List[Dict]:
        """Current item balances per warehouse, including stock value."""
        try:
            from core.services.warehouse_service import warehouse_service
            rows = warehouse_service.balances(search=search, warehouse_id=warehouse_id)
            return rows if isinstance(rows, list) else []
        except Exception:
            return []

    def warehouse_movements(self, warehouse_id: int | None = None, item_id: int | None = None, limit: int = 500) -> List[Dict]:
        """Latest warehouse movements for reporting."""
        try:
            from core.services.warehouse_service import warehouse_service
            rows = warehouse_service.movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit)
            return rows if isinstance(rows, list) else []
        except Exception:
            return []

    def warehouse_transfers(self, limit: int = 500) -> List[Dict]:
        """Warehouse transfer log."""
        try:
            from core.services.warehouse_service import warehouse_service
            rows = warehouse_service.transfers(limit=limit)
            return rows if isinstance(rows, list) else []
        except Exception:
            return []

    def warehouse_valuation(self, warehouse_id: int | None = None) -> Dict:
        """Inventory valuation grouped by warehouse and grand total."""
        balances = self.warehouse_balances(warehouse_id=warehouse_id)
        from decimal import Decimal
        warehouses: Dict[str, Dict] = {}
        grand_total = Decimal('0')
        for row in balances:
            wh_name = row.get('warehouse_name') or 'غير محدد'
            qty = Decimal(str(row.get('quantity') or 0))
            avg = Decimal(str(row.get('average_cost') or row.get('unit_cost') or 0))
            value = Decimal(str(row.get('stock_value') if row.get('stock_value') is not None else qty * avg))
            bucket = warehouses.setdefault(wh_name, {'warehouse_name': wh_name, 'item_count': 0, 'total_qty': Decimal('0'), 'total_value': Decimal('0')})
            bucket['item_count'] += 1
            bucket['total_qty'] += qty
            bucket['total_value'] += value
            grand_total += value
        return {'warehouses': list(warehouses.values()), 'grand_total': grand_total, 'balances': balances}


    # ========== Cash / Bank reports ==========
    def cashboxes_report(self) -> List[Dict]:
        """Cashbox balances for financial reporting."""
        try:
            from core.services.cashbox_service import cashbox_service
            return cashbox_service.cashboxes(include_archived=False)
        except Exception:
            return []

    def bank_accounts_report(self) -> List[Dict]:
        """Bank account balances for financial reporting."""
        try:
            from core.services.cashbox_service import cashbox_service
            return cashbox_service.bank_accounts(include_archived=False)
        except Exception:
            return []

    def cash_bank_movements(self, cashbox_id: int | None = None, bank_account_id: int | None = None, limit: int = 1000) -> List[Dict]:
        """Unified cash/bank movement ledger."""
        try:
            from core.services.cashbox_service import cashbox_service
            return cashbox_service.movements(limit=limit, cashbox_id=cashbox_id, bank_account_id=bank_account_id)
        except Exception:
            return []

    def pos_shifts_report(self, limit: int = 1000, status: str | None = None) -> List[Dict]:
        """POS shift report."""
        try:
            from core.services.cashbox_service import cashbox_service
            return cashbox_service.shifts(limit=limit, status=status)
        except Exception:
            return []

    def cash_bank_summary(self) -> Dict:
        """Financial liquidity summary from cashboxes and bank accounts."""
        from decimal import Decimal
        cashboxes = self.cashboxes_report()
        banks = self.bank_accounts_report()
        cash_total = sum(Decimal(str(c.get('balance') or 0)) for c in cashboxes)
        bank_total = sum(Decimal(str(b.get('balance') or 0)) for b in banks)
        return {
            'cash_total': cash_total,
            'bank_total': bank_total,
            'available_total': cash_total + bank_total,
            'cashbox_count': len(cashboxes),
            'bank_count': len(banks),
        }


reporting_service = ReportingService()
