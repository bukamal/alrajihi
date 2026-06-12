# -*- coding: utf-8 -*-
"""User/auth gateway contract and factory."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class UserGateway(ABC):
    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_users(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create_user(self, username: str, password: str, full_name: str, role: str, branch_id=None) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user_id: str, full_name: str, role: str, branch_id=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        raise NotImplementedError


def create_user_gateway() -> UserGateway:
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.user_gateway import RemoteUserGateway
        return RemoteUserGateway(db.get_rest_client())
    from gateways.local.user_gateway import LocalUserGateway
    return LocalUserGateway()
