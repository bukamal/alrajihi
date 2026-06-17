# -*- coding: utf-8 -*-
"""Enterprise RBAC service (Phase 157).

Provides a database-backed roles/permissions layer while preserving the legacy
`users.role` field as a compatibility fallback.  All methods are defensive so
permission checks never crash the UI if a migration is still pending.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional

from auth.session import UserSession


DEFAULT_ROLE_PERMISSIONS = {
    'admin': None,  # all permissions
    'manager': {
        'reports.view', 'reports.export', 'invoices.edit', 'returns.edit',
        'branches.view_all', 'approval.submit', 'approval.approve', 'approval.reject'
    },
    'accountant': {
        'reports.view', 'reports.export', 'accounting.view', 'accounting.post',
        'accounting.close_period', 'approval.submit'
    },
    'cashier': {'approval.submit'},
    'viewer': {'reports.view'},
}

ACTION_PERMISSION_MAP = {
    'hide_profit': 'reports.view',
    'delete_records': 'invoices.delete',
    'edit_invoices': 'invoices.edit',
    'edit_returns': 'returns.edit',
    'view_reports': 'reports.view',
    'export_reports': 'reports.export',
    'view_all_branches': 'branches.view_all',
    'manage_all_branches': 'branches.manage_all',
    'approval.submit': 'approval.submit',
    'approval.approve': 'approval.approve',
    'approval.reject': 'approval.reject',
    'accounting.view': 'accounting.view',
    'accounting.post': 'accounting.post',
    'accounting.close_period': 'accounting.close_period',
    'settings.manage': 'settings.manage',
    'users.manage': 'users.manage',
    'system.health.view': 'system.health.view',
    'system.validation.run': 'system.validation.run',
    'approval.matrix.manage': 'approval.matrix.manage',
    'approval.level1': 'approval.level1',
    'approval.level2': 'approval.level2',
    'approval.level3': 'approval.level3',
}


class RBACService:
    def __init__(self, gateway=None):
        self.gateway = gateway or self._create_gateway()

    def _create_gateway(self):
        from gateways.rbac_gateway import create_rbac_gateway
        return create_rbac_gateway()

    def _user_id(self, user_id: str | None = None) -> str | None:
        return str(user_id or UserSession.get_current_user_id() or '') or None

    def _legacy_role(self, user_id: str | None = None) -> str:
        current = UserSession.get_current() or {}
        if user_id is None and current.get('role'):
            return str(current.get('role')).lower()
        try:
            return self.gateway.legacy_role(user_id)
        except Exception:
            return 'admin'

    def list_roles(self) -> List[Dict]:
        try:
            return self.gateway.list_roles()
        except Exception:
            return []

    def list_permissions(self) -> List[Dict]:
        try:
            return self.gateway.list_permissions()
        except Exception:
            return []

    def user_roles(self, user_id: str | None = None) -> List[str]:
        uid = self._user_id(user_id)
        try:
            roles = self.gateway.user_roles(uid)
            if roles:
                return roles
        except Exception:
            pass
        return [self._legacy_role(user_id)]

    def role_parent_map(self) -> dict[str, str]:
        try:
            return self.gateway.role_parent_map()
        except Exception:
            return {}

    def effective_user_roles(self, user_id: str | None = None) -> List[str]:
        roles = [str(r).lower() for r in self.user_roles(user_id)]
        parent_map = self.role_parent_map()
        seen = set(roles)
        stack = list(roles)
        while stack:
            role = stack.pop()
            parent = parent_map.get(role)
            if parent and parent not in seen:
                seen.add(parent)
                stack.append(parent)
        return sorted(seen)

    def role_permissions(self, role_name: str) -> set[str]:
        try:
            perms = self.gateway.role_permissions(role_name)
            if perms:
                return perms
        except Exception:
            pass
        defaults = DEFAULT_ROLE_PERMISSIONS.get(str(role_name).lower(), set())
        return {'*'} if defaults is None else set(defaults)

    def can_access_branch(self, branch_id: int | None, user_id: str | None = None) -> bool:
        if branch_id in (None, '', 0):
            return True
        if self.has_permission('branches.view_all', user_id):
            return True
        allowed = self.allowed_branch_ids(user_id)
        try:
            return int(branch_id) in allowed
        except Exception:
            return False

    def user_permissions(self, user_id: str | None = None) -> set[str]:
        roles = self.effective_user_roles(user_id)
        if 'admin' in roles:
            return {p['key'] for p in self.list_permissions()} or {'*'}
        perms: set[str] = set()
        try:
            uid = self._user_id(user_id)
            perms.update(self.gateway.user_direct_permissions(uid))
        except Exception:
            pass
        if not perms:
            for role in roles:
                defaults = DEFAULT_ROLE_PERMISSIONS.get(role, set())
                if defaults is None:
                    return {'*'}
                perms.update(defaults)
        return perms

    def has_permission(self, permission_key: str, user_id: str | None = None) -> bool:
        key = ACTION_PERMISSION_MAP.get(permission_key, permission_key)
        perms = self.user_permissions(user_id)
        return '*' in perms or key in perms

    def can_action(self, action: str, user_id: str | None = None) -> bool:
        return self.has_permission(ACTION_PERMISSION_MAP.get(action, action), user_id)

    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        try:
            return self.gateway.assign_roles(user_id, role_names)
        except Exception:
            return False

    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        try:
            return self.gateway.set_role_permissions(role_name, permission_keys)
        except Exception:
            return False

    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        try:
            return self.gateway.set_user_branches(user_id, branch_ids)
        except Exception:
            return False

    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        uid = self._user_id(user_id)
        try:
            return self.gateway.allowed_branch_ids(uid)
        except Exception:
            return []


rbac_service = RBACService()
