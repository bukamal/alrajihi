# -*- coding: utf-8 -*-
"""RBAC gateway contract and factory.

Keeps roles/permissions persistence behind the gateway boundary so
core/services do not touch DatabaseConnection or SQL directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional


class RBACGateway(ABC):
    @abstractmethod
    def legacy_role(self, user_id: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_roles(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def list_permissions(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def user_roles(self, user_id: str | None = None) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def role_parent_map(self) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def role_permissions(self, role_name: str) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def user_direct_permissions(self, user_id: str | None = None) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        raise NotImplementedError


class NullRBACGateway(RBACGateway):
    """Remote/unavailable fallback; service-level defaults remain authoritative."""

    def legacy_role(self, user_id: str | None = None) -> str:
        return "admin"

    def list_roles(self) -> List[Dict]:
        return []

    def list_permissions(self) -> List[Dict]:
        return []

    def user_roles(self, user_id: str | None = None) -> List[str]:
        return []

    def role_parent_map(self) -> dict[str, str]:
        return {}

    def role_permissions(self, role_name: str) -> set[str]:
        return set()

    def user_direct_permissions(self, user_id: str | None = None) -> set[str]:
        return set()

    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        return False

    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        return False

    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        return False

    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        return []


def create_rbac_gateway() -> RBACGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        return NullRBACGateway()

    from gateways.local.rbac_gateway import LocalRBACGateway
    return LocalRBACGateway(db.get_connection())
