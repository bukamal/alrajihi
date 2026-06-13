# -*- coding: utf-8 -*-
"""Local branch gateway adapter.

This is the only gateway layer allowed to use the legacy branch DAO.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.compat import records
from database.dao.branch_dao import branch_dao
from gateways.branch_gateway import BranchGateway


class LocalBranchGateway(BranchGateway):
    def bootstrap(self) -> None:
        branch_dao.bootstrap_defaults()

    def list(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return records(branch_dao.get_all(include_archived=include_archived), 'branches')

    def get(self, branch_id: int) -> Optional[Dict[str, Any]]:
        branch = branch_dao.get_by_id(branch_id)
        return branch if isinstance(branch, dict) else None

    def default_branch_id(self) -> int | None:
        return branch_dao.default_branch_id()

    def create(self, data: Dict[str, Any]) -> int:
        return branch_dao.add(data)

    def update(self, branch_id: int, data: Dict[str, Any]):
        return branch_dao.update(branch_id, data)

    def archive(self, branch_id: int):
        return branch_dao.delete(branch_id)

    def is_remote(self) -> bool:
        return False
