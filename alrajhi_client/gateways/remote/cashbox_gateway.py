# -*- coding: utf-8 -*-
"""Remote API cashbox/bank gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from gateways.cashbox_gateway import CashboxGateway


class RemoteCashboxGateway(CashboxGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def bootstrap(self) -> None:
        # Defaults are server-side responsibility in remote mode.
        return None

    def cashboxes(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return self.rest_client.get_cashboxes(include_archived=include_archived)

    def bank_accounts(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return self.rest_client.get_bank_accounts(include_archived=include_archived)

    def get_cashbox(self, cashbox_id: int) -> Optional[Dict[str, Any]]:
        cashbox = self.rest_client.get_cashbox(cashbox_id)
        return cashbox if isinstance(cashbox, dict) else None

    def get_bank_account(self, bank_account_id: int) -> Optional[Dict[str, Any]]:
        account = self.rest_client.get_bank_account(bank_account_id)
        return account if isinstance(account, dict) else None

    def default_cashbox_id(self, branch_id: int | None = None) -> Optional[int]:
        return self.rest_client.default_cashbox_id(branch_id)

    def add_cashbox(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_cashbox(data)

    def update_cashbox(self, cashbox_id: int, data: Dict[str, Any]):
        return self.rest_client.update_cashbox(cashbox_id, data)

    def archive_cashbox(self, cashbox_id: int):
        return self.rest_client.archive_cashbox(cashbox_id)

    def add_bank_account(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_bank_account(data)

    def update_bank_account(self, bank_account_id: int, data: Dict[str, Any]):
        return self.rest_client.update_bank_account(bank_account_id, data)

    def archive_bank_account(self, bank_account_id: int):
        return self.rest_client.archive_bank_account(bank_account_id)

    def movements(self, limit: int = 200, cashbox_id: int | None = None,
                  bank_account_id: int | None = None) -> List[Dict[str, Any]]:
        return self.rest_client.get_cash_bank_movements(limit=limit, cashbox_id=cashbox_id, bank_account_id=bank_account_id)

    def record_movement(self, data: Dict[str, Any]) -> int | None:
        return self.rest_client.add_cash_bank_movement(data)

    def delete_reference_movements(self, reference_type, reference_id):
        return self.rest_client.delete_reference_movements(reference_type, reference_id)

    def current_open_shift(self, cashbox_id: int | None = None):
        return self.rest_client.current_open_shift(cashbox_id)

    def shifts(self, limit: int = 100, status: str | None = None) -> List[Dict[str, Any]]:
        return self.rest_client.get_shifts(limit=limit, status=status)

    def open_shift(self, data: Dict[str, Any]) -> int | None:
        return self.rest_client.open_shift(data)

    def shift_summary(self, shift_id: int):
        return self.rest_client.shift_summary(shift_id)

    def close_shift(self, shift_id: int, actual_amount, notes: str = ''):
        return self.rest_client.close_shift(shift_id, actual_amount, notes)
