# -*- coding: utf-8 -*-
"""Branch gateway contract and factory.

Application services use this contract instead of importing branch DAO or
RestClient directly.  Local persistence stays behind the local adapter; remote
mode stays behind the remote adapter.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BranchGateway(ABC):
    @abstractmethod
    def bootstrap(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get(self, branch_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def default_branch_id(self) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, branch_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def archive(self, branch_id: int):
        raise NotImplementedError


def create_branch_gateway() -> BranchGateway:
    """Return the active branch gateway."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.branch_gateway import RemoteBranchGateway
        return RemoteBranchGateway(db.get_rest_client())

    from gateways.local.branch_gateway import LocalBranchGateway
    return LocalBranchGateway()
