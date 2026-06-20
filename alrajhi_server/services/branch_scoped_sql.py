# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from alrajhi_server.services.branch_access_policy import branch_access_policy


def invoice_scope(user_id: Any, alias: str = 'i', requested_branch_id: Any = None) -> tuple[str, list[Any]]:
    return branch_access_policy.scope_sql(user_id, alias=alias, branch_column='branch_id', requested_branch_id=requested_branch_id)


def return_scope(user_id: Any, alias: str, requested_branch_id: Any = None) -> tuple[str, list[Any]]:
    return branch_access_policy.scope_sql(user_id, alias=alias, branch_column='branch_id', requested_branch_id=requested_branch_id)


def warehouse_scope(user_id: Any, alias: str = 'w', requested_branch_id: Any = None) -> tuple[str, list[Any]]:
    return branch_access_policy.scope_sql(user_id, alias=alias, branch_column='branch_id', requested_branch_id=requested_branch_id)


def cashbox_scope(user_id: Any, alias: str = 'c', requested_branch_id: Any = None) -> tuple[str, list[Any]]:
    return branch_access_policy.scope_sql(user_id, alias=alias, branch_column='branch_id', requested_branch_id=requested_branch_id)


def restaurant_scope(user_id: Any, alias: str = 's', requested_branch_id: Any = None) -> tuple[str, list[Any]]:
    return branch_access_policy.scope_sql(user_id, alias=alias, branch_column='branch_id', requested_branch_id=requested_branch_id)


__all__ = ['invoice_scope', 'return_scope', 'warehouse_scope', 'cashbox_scope', 'restaurant_scope']
