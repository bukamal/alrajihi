# -*- coding: utf-8 -*-
"""Local user gateway adapter."""
from __future__ import annotations

from typing import Dict, List, Optional

from database import UserRepository
from gateways.user_gateway import UserGateway


class LocalUserGateway(UserGateway):
    def __init__(self):
        self.repo = UserRepository()

    def is_remote(self) -> bool:
        return False

    def list_users(self) -> List[Dict]:
        return self.repo.get_all()

    def get_user(self, user_id: str) -> Optional[Dict]:
        return self.repo.get_by_id(user_id)

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        return self.repo.authenticate(username, password)

    def create_user(self, username: str, password: str, full_name: str, role: str, branch_id=None) -> str:
        return self.repo.create(username, password, full_name, role, branch_id)

    def update_user(self, user_id: str, full_name: str, role: str, branch_id=None) -> None:
        self.repo.update(user_id, full_name, role, branch_id)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        return self.repo.change_password(user_id, old_password, new_password)

    def delete_user(self, user_id: str) -> bool:
        return self.repo.delete(user_id)
