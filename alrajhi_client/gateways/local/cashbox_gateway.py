# -*- coding: utf-8 -*-
"""Local cashbox/bank gateway adapter.

This is the only gateway layer allowed to use the legacy cashbox DAO.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.compat import records
from database.dao.cashbox_dao import cashbox_dao
from gateways.cashbox_gateway import CashboxGateway


class LocalCashboxGateway(CashboxGateway):
    def bootstrap(self) -> None:
        cashbox_dao.bootstrap_defaults()

    def cashboxes(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return records(cashbox_dao.get_cashboxes(include_archived), 'cashboxes')

    def bank_accounts(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return records(cashbox_dao.get_bank_accounts(include_archived), 'bank_accounts')

    def get_cashbox(self, cashbox_id: int) -> Optional[Dict[str, Any]]:
        cashbox = cashbox_dao.get_cashbox(cashbox_id)
        return cashbox if isinstance(cashbox, dict) else None

    def get_bank_account(self, bank_account_id: int) -> Optional[Dict[str, Any]]:
        account = cashbox_dao.get_bank_account(bank_account_id)
        return account if isinstance(account, dict) else None

    def default_cashbox_id(self, branch_id: int | None = None) -> Optional[int]:
        return cashbox_dao.default_cashbox_id(branch_id)

    def add_cashbox(self, data: Dict[str, Any]) -> int:
        return cashbox_dao.add_cashbox(data)

    def update_cashbox(self, cashbox_id: int, data: Dict[str, Any]):
        return cashbox_dao.update_cashbox(cashbox_id, data)

    def archive_cashbox(self, cashbox_id: int):
        return cashbox_dao.archive_cashbox(cashbox_id)

    def add_bank_account(self, data: Dict[str, Any]) -> int:
        return cashbox_dao.add_bank_account(data)

    def update_bank_account(self, bank_account_id: int, data: Dict[str, Any]):
        return cashbox_dao.update_bank_account(bank_account_id, data)

    def archive_bank_account(self, bank_account_id: int):
        return cashbox_dao.archive_bank_account(bank_account_id)

    def movements(self, limit: int = 200, cashbox_id: int | None = None,
                  bank_account_id: int | None = None) -> List[Dict[str, Any]]:
        return records(cashbox_dao.movements(limit=limit, cashbox_id=cashbox_id, bank_account_id=bank_account_id), 'movements')

    def record_movement(self, data: Dict[str, Any]) -> int | None:
        return cashbox_dao.record_movement(data)

    def delete_reference_movements(self, reference_type, reference_id):
        return cashbox_dao.delete_reference_movements(reference_type, reference_id)

    def current_open_shift(self, cashbox_id: int | None = None):
        return cashbox_dao.current_open_shift(cashbox_id)

    def shifts(self, limit: int = 100, status: str | None = None) -> List[Dict[str, Any]]:
        return records(cashbox_dao.shifts(limit, status), 'shifts')

    def open_shift(self, data: Dict[str, Any]) -> int | None:
        return cashbox_dao.open_shift(data)

    def shift_summary(self, shift_id: int):
        return cashbox_dao.shift_summary(shift_id)

    def close_shift(self, shift_id: int, actual_amount, notes: str = ''):
        return cashbox_dao.close_shift(shift_id, actual_amount, notes)
