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

    # ========== Phase150: Branch-scoped reporting governance ==========
    def _effective_branch_id(self, branch_id=None):
        try:
            from core.services.permission_service import permission_service
            return permission_service.effective_branch_id(branch_id)
        except Exception:
            return branch_id

    def _warehouse_ids_for_branch(self, branch_id=None):
        try:
            from core.services.branch_service import branch_service
            return branch_service.warehouses_for_scope(branch_id)
        except Exception:
            return []

    def branch_report_scope(self, branch_id=None) -> Dict:
        try:
            from core.services.branch_service import branch_service
            return branch_service.report_scope(branch_id)
        except Exception:
            return {'mode': 'all', 'branch_id': None, 'branch_name': ''}

    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.summary(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.income_statement(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.balance_sheet(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def customer_statement(self, customer_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict]:
        result = self._gateway.customer_statement(customer_id, start_date, end_date)
        return result if isinstance(result, list) else []

    def supplier_statement(self, supplier_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict]:
        result = self._gateway.supplier_statement(supplier_id, start_date, end_date)
        return result if isinstance(result, list) else []

    def customer_balances(self) -> List[Dict]:
        result = self._gateway.customer_balances()
        return result if isinstance(result, list) else []

    def supplier_balances(self) -> List[Dict]:
        result = self._gateway.supplier_balances()
        return result if isinstance(result, list) else []

    def customer_aging(self, as_of_date: str | None = None) -> List[Dict]:
        result = self._gateway.customer_aging(as_of_date)
        return result if isinstance(result, list) else []

    def supplier_aging(self, as_of_date: str | None = None) -> List[Dict]:
        result = self._gateway.supplier_aging(as_of_date)
        return result if isinstance(result, list) else []

    def trial_balance(self) -> List[Dict]:
        result = self._gateway.trial_balance()
        return result if isinstance(result, list) else []

    def accounting_trial_balance(self) -> List[Dict]:
        """Real double-entry trial balance from journal_lines."""
        try:
            from core.services.accounting_service import accounting_service
            rows = accounting_service.trial_balance()
            return rows if isinstance(rows, list) else []
        except Exception:
            return []

    def accounting_ledger(self, account_id=None, start_date=None, end_date=None, limit: int = 1000) -> List[Dict]:
        """Real account ledger from journal_lines."""
        try:
            from core.services.accounting_service import accounting_service
            rows = accounting_service.ledger(account_id=account_id, start_date=start_date, end_date=end_date, limit=limit)
            return rows if isinstance(rows, list) else []
        except Exception:
            return []


    def accounting_income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        try:
            from core.services.accounting_service import accounting_service
            result = accounting_service.income_statement(start_date=start_date, end_date=end_date)
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    def accounting_balance_sheet(self, as_of_date: str | None = None) -> Dict:
        try:
            from core.services.accounting_service import accounting_service
            result = accounting_service.balance_sheet(as_of_date=as_of_date)
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    def accounting_cash_flow(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        try:
            from core.services.accounting_service import accounting_service
            result = accounting_service.cash_flow(start_date=start_date, end_date=end_date)
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}


    # ========== Warehouse reports ==========
    def warehouse_balances(self, warehouse_id: int | None = None, search: str | None = None, branch_id: int | None = None) -> List[Dict]:
        """Current item balances per warehouse, including stock value."""
        try:
            from core.services.warehouse_service import warehouse_service
            rows = warehouse_service.balances(search=search, warehouse_id=warehouse_id)
            if not isinstance(rows, list):
                return []
            eff_branch = self._effective_branch_id(branch_id)
            if eff_branch:
                rows = [r for r in rows if int(r.get('branch_id') or 0) == int(eff_branch)]
            return rows
        except Exception:
            return []

    def warehouse_movements(self, warehouse_id: int | None = None, item_id: int | None = None, limit: int = 500, branch_id: int | None = None) -> List[Dict]:
        """Latest warehouse movements for reporting."""
        try:
            from core.services.warehouse_service import warehouse_service
            rows = warehouse_service.movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit)
            if not isinstance(rows, list):
                return []
            eff_branch = self._effective_branch_id(branch_id)
            if eff_branch:
                wh_ids = set(self._warehouse_ids_for_branch(eff_branch))
                rows = [r for r in rows if int(r.get('warehouse_id') or 0) in wh_ids]
            return rows
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

    def warehouse_valuation(self, warehouse_id: int | None = None, branch_id: int | None = None) -> Dict:
        """Inventory valuation grouped by warehouse and grand total."""
        balances = self.warehouse_balances(warehouse_id=warehouse_id, branch_id=branch_id)
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
        """Financial liquidity summary from cashboxes and bank accounts.

        Remote and legacy adapters do not always agree on the balance field
        name.  The dashboard and reports must therefore normalize all known
        names before falling back to zero.
        """
        from decimal import Decimal

        def _amount(row, *keys):
            if not isinstance(row, dict):
                return Decimal('0')
            for key in keys:
                value = row.get(key)
                if value not in (None, ''):
                    try:
                        return Decimal(str(value or 0))
                    except Exception:
                        return Decimal('0')
            return Decimal('0')

        cashboxes = self.cashboxes_report()
        banks = self.bank_accounts_report()
        cash_total = sum((_amount(c, 'balance', 'current_balance', 'cash_balance', 'amount') for c in cashboxes), Decimal('0'))
        bank_total = sum((_amount(b, 'balance', 'current_balance', 'account_balance', 'amount') for b in banks), Decimal('0'))
        return {
            'cash_total': cash_total,
            'bank_total': bank_total,
            'available_total': cash_total + bank_total,
            'cashbox_count': len(cashboxes),
            'bank_count': len(banks),
            'cashboxes': cashboxes,
            'bank_accounts': banks,
        }


    # ========== Phase139: Item movement and invoice profitability ==========
    def item_movement_report(self, item_id: int | None = None, warehouse_id: int | None = None,
                             start_date: str | None = None, end_date: str | None = None,
                             limit: int = 2000, branch_id: int | None = None) -> List[Dict]:
        result = self._gateway.item_movement_report(
            item_id=item_id,
            warehouse_id=warehouse_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            branch_id=self._effective_branch_id(branch_id),
        )
        return result if isinstance(result, list) else []

    def invoice_profit_report(self, start_date: str | None = None, end_date: str | None = None,
                              customer_id: int | None = None, limit: int = 2000, branch_id: int | None = None) -> List[Dict]:
        result = self._gateway.invoice_profit_report(
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            limit=limit,
            branch_id=self._effective_branch_id(branch_id),
        )
        return result if isinstance(result, list) else []


    # ========== Phase140: Cash/bank ledger, net profit, manufacturing reports ==========
    def net_profit_report(self, start_date: str | None = None, end_date: str | None = None, branch_id: int | None = None) -> Dict:
        result = self._gateway.net_profit_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=self._effective_branch_id(branch_id),
        )
        return result if isinstance(result, dict) else {}

    def manufacturing_orders_report(self, start_date: str | None = None, end_date: str | None = None, status: str | None = None) -> List[Dict]:
        result = self._gateway.manufacturing_orders_report(start_date=start_date, end_date=end_date, status=status)
        return result if isinstance(result, list) else []

    def product_cost_report(self, search: str | None = None, limit: int = 1000, branch_id: int | None = None, item_id: int | None = None) -> List[Dict]:
        try:
            result = self._gateway.product_cost_report(search=search, limit=limit, branch_id=self._effective_branch_id(branch_id), item_id=item_id)
        except TypeError:
            result = self._gateway.product_cost_report(search=search, limit=limit, branch_id=self._effective_branch_id(branch_id))
        return result if isinstance(result, list) else []


    # ========== Phase141: Full accounting and smart inventory reports ==========


    def general_ledger_report(self, account_id: int | None = None, start_date: str | None = None,
                              end_date: str | None = None, limit: int = 2000) -> List[Dict]:
        result = self._gateway.general_ledger_report(account_id=account_id, start_date=start_date, end_date=end_date, limit=limit)
        return result if isinstance(result, list) else []

    def full_trial_balance_report(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._gateway.full_trial_balance_report(start_date=start_date, end_date=end_date)
        return result if isinstance(result, dict) else {}

    def smart_items_report(self, kind: str, start_date: str | None = None, end_date: str | None = None,
                           warehouse_id: int | None = None, limit: int = 500, branch_id: int | None = None) -> List[Dict]:
        result = self._gateway.smart_items_report(
            kind=kind,
            start_date=start_date,
            end_date=end_date,
            warehouse_id=warehouse_id,
            limit=limit,
            branch_id=self._effective_branch_id(branch_id),
        )
        return result if isinstance(result, list) else []

    def report_consistency_audit(self, start_date: str | None = None, end_date: str | None = None) -> List[Dict]:
        """Lightweight consistency audit between reports and source ledgers."""
        try:
            from decimal import Decimal
            results=[]
            tb=self.full_trial_balance_report(start_date, end_date)
            results.append({'scope':'trial_balance','status':'PASS' if tb.get('balanced') else 'FAIL','message':f"difference={tb.get('difference')}", 'severity':'high' if not tb.get('balanced') else 'info'})
            np=self.net_profit_report(start_date, end_date)
            inv=self.invoice_profit_report(start_date, end_date)
            inv_profit=sum((Decimal(str(r.get('profit') or 0)) for r in inv), Decimal('0'))
            net=Decimal(str(np.get('net_profit') or 0)) if np else Decimal('0')
            diff=inv_profit-net
            results.append({'scope':'profit','status':'PASS' if abs(diff) < Decimal('0.01') else 'WARN','message':f"invoice_profit={inv_profit}; net_profit={net}; diff={diff}", 'severity':'medium'})
            return results
        except Exception as exc:
            return [{'scope':'audit','status':'FAIL','message':str(exc),'severity':'high'}]


reporting_service = ReportingService()
