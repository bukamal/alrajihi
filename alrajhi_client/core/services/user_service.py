# -*- coding: utf-8 -*-
"""User/auth application service."""
from __future__ import annotations

from typing import Dict, List, Optional

from gateways.user_gateway import create_user_gateway


class UserService:
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            self._gateway = create_user_gateway()
        return self._gateway

    def _policy(self):
        from core.services.user_operation_policy import user_operation_policy
        return user_operation_policy

    def _require(self, operation: str, context: str = '') -> None:
        self._policy().require(operation, context=context or 'UserService')

    def is_remote(self) -> bool:
        return self._get_gateway().is_remote()

    def list_users(self) -> List[Dict]:
        self._require(self._policy().OP_USE, 'UserService.list_users')
        return self._get_gateway().list_users()

    def get_user(self, user_id: str) -> Optional[Dict]:
        self._require(self._policy().OP_USE, 'UserService.get_user')
        return self._get_gateway().get_user(user_id)

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        return self._get_gateway().authenticate(username, password)

    def create_user(self, username: str, password: str, full_name: str, role: str, branch_id=None) -> str:
        self._require(self._policy().OP_CREATE, 'UserService.create_user')
        return self._get_gateway().create_user(username, password, full_name, role, branch_id)

    def update_user(self, user_id: str, full_name: str, role: str, branch_id=None) -> None:
        self._require(self._policy().OP_EDIT, 'UserService.update_user')
        self._get_gateway().update_user(user_id, full_name, role, branch_id)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        self._require(self._policy().OP_CHANGE_PASSWORD, 'UserService.change_password')
        return self._get_gateway().change_password(user_id, old_password, new_password)

    def delete_user(self, user_id: str) -> bool:
        self._require(self._policy().OP_DELETE, 'UserService.delete_user')
        return self._get_gateway().delete_user(user_id)


user_service = UserService()
