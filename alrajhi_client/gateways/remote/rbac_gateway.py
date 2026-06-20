# -*- coding: utf-8 -*-
"""Remote RBAC gateway backed by the Flask /api/rbac endpoints.

Phase260 makes RBAC network-ready.  Previously create_rbac_gateway() returned a
NullRBACGateway in client/server mode, so document-shell permission checks could
only fall back to local legacy settings.  This adapter keeps role, permission and
branch decisions aligned with the server.
"""
from __future__ import annotations

from typing import Dict, Iterable, List

from gateways.rbac_gateway import RBACGateway


class RemoteRBACGateway(RBACGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def is_remote(self) -> bool:
        return True

    def legacy_role(self, user_id: str | None = None) -> str:
        try:
            roles = self.user_roles(user_id)
            return str(roles[0]).lower() if roles else "user"
        except Exception:
            return "user"

    def list_roles(self) -> List[Dict]:
        return list(self.rest_client.get_rbac_roles() or [])

    def list_permissions(self) -> List[Dict]:
        return list(self.rest_client.get_rbac_permissions() or [])

    def _me(self) -> Dict:
        return dict(self.rest_client.get_my_permissions() or {})

    def user_roles(self, user_id: str | None = None) -> List[str]:
        # The server intentionally exposes /api/rbac/me for the current token.
        # Admin-only user-specific reads remain available in the server API, but
        # the current UI permission checks only need the active user.
        data = self._me()
        return [str(r).lower() for r in data.get("roles", []) if str(r).strip()]

    def role_parent_map(self) -> dict[str, str]:
        # Current server API does not expose role inheritance. Returning empty is
        # explicit and safe; role inheritance remains local-only until an endpoint
        # is added.
        return {}

    def role_permissions(self, role_name: str) -> set[str]:
        rows = self.rest_client._request('GET', f'/api/rbac/roles/{role_name}/permissions') or []
        result: set[str] = set()
        for row in rows:
            try:
                if int(row.get('allowed', 0)) == 1:
                    result.add(str(row.get('key') or row.get('permission_key')))
            except Exception:
                continue
        return {x for x in result if x}

    def user_direct_permissions(self, user_id: str | None = None) -> set[str]:
        data = self._me()
        return {str(p) for p in data.get("permissions", []) if str(p).strip()}

    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        self.rest_client.set_user_roles(str(user_id), [str(r).strip().lower() for r in role_names if str(r).strip()])
        return True

    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        self.rest_client.set_role_permissions(str(role_name).strip().lower(), [str(k).strip() for k in permission_keys if str(k).strip()])
        return True

    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        self.rest_client.set_user_branch_access(str(user_id), [int(b) for b in branch_ids])
        return True

    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        data = self._me()
        result: List[int] = []
        for value in data.get("branch_ids", []) or []:
            try:
                result.append(int(value))
            except Exception:
                continue
        return result
