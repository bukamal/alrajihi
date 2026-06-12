# -*- coding: utf-8 -*-
"""Remote user gateway adapter."""
from __future__ import annotations

from typing import Dict, List, Optional

from gateways.user_gateway import UserGateway


class RemoteUserGateway(UserGateway):
    def __init__(self, client):
        self.client = client

    def is_remote(self) -> bool:
        return True

    def list_users(self) -> List[Dict]:
        return self.client.get_users()

    def get_user(self, user_id: str) -> Optional[Dict]:
        for user in self.list_users():
            if str(user.get('id')) == str(user_id):
                return user
        return None

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        return self.client.login(username, password)

    def create_user(self, username: str, password: str, full_name: str, role: str, branch_id=None) -> str:
        return str(self.client.add_user({
            'username': username,
            'password': password,
            'full_name': full_name,
            'role': role,
            'branch_id': branch_id,
        }))

    def update_user(self, user_id: str, full_name: str, role: str, branch_id=None) -> None:
        self.client.update_user(int(user_id), {'full_name': full_name, 'role': role, 'branch_id': branch_id})

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            self.client.change_password(old_password, new_password)
            return True
        except Exception:
            return False

    def delete_user(self, user_id: str) -> bool:
        if str(user_id) in {'1', 'admin'}:
            return False
        try:
            self.client.delete_user(int(user_id))
            return True
        except Exception:
            return False
