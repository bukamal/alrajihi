# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Iterable

from alrajhi_server.repositories.rbac_repository import get_rbac_repository


class BranchAccessError(PermissionError):
    pass


def _to_int(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        return int(value)
    except Exception:
        return None


class ServerBranchAccessPolicy:
    """Server-side branch access helper for API repositories/routes.

    It centralizes the rules behind ``user_branch_access``.  Routes can use
    ``scope_sql`` for list/report queries and ``require`` before mutating a
    branch-bound resource.  The helper is deliberately SQLite-agnostic and keeps
    the returned SQL fragment small enough to embed in existing route SQL.
    """

    def __init__(self):
        self.repo = get_rbac_repository()

    def is_admin(self, user_id: Any) -> bool:
        try:
            return bool(self.repo.is_admin(str(user_id)))
        except Exception:
            return False

    def can_view_all_branches(self, user_id: Any) -> bool:
        if self.is_admin(user_id):
            return True
        try:
            return "branches.view_all" in set(self.repo.list_user_permissions(str(user_id)))
        except Exception:
            return False

    def allowed_branch_ids(self, user_id: Any) -> list[int]:
        try:
            return [int(x) for x in self.repo.list_user_branch_ids(str(user_id))]
        except Exception:
            return []

    def can_access(self, user_id: Any, branch_id: Any) -> bool:
        bid = _to_int(branch_id)
        if bid is None:
            return True
        if self.can_view_all_branches(user_id):
            return True
        allowed = set(self.allowed_branch_ids(user_id))
        return not allowed or bid in allowed

    def require(self, user_id: Any, branch_id: Any, *, context: str = "") -> int | None:
        bid = _to_int(branch_id)
        if bid is not None and not self.can_access(user_id, bid):
            suffix = f" in {context}" if context else ""
            raise BranchAccessError(f"Branch access denied for branch_id={bid}{suffix}")
        return bid

    def effective_branch_id(self, user_id: Any, requested_branch_id: Any = None) -> int | None:
        requested = _to_int(requested_branch_id)
        if requested is not None and self.can_view_all_branches(user_id):
            return requested
        if requested is not None and self.can_access(user_id, requested):
            return requested
        allowed = self.allowed_branch_ids(user_id)
        return int(allowed[0]) if allowed and not self.can_view_all_branches(user_id) else None

    def scope_sql(self, user_id: Any, *, alias: str = "", branch_column: str = "branch_id", requested_branch_id: Any = None) -> tuple[str, list[Any]]:
        column = f"{alias}.{branch_column}" if alias else branch_column
        requested = _to_int(requested_branch_id)
        if self.can_view_all_branches(user_id):
            if requested is None:
                return "", []
            return f" AND {column}=?", [requested]
        allowed = self.allowed_branch_ids(user_id)
        if requested is not None and requested in allowed:
            return f" AND {column}=?", [requested]
        if not allowed:
            # Backward compatibility for old single-branch users not yet migrated.
            return "", []
        placeholders = ",".join("?" for _ in allowed)
        return f" AND ({column} IS NULL OR {column} IN ({placeholders}))", allowed


branch_access_policy = ServerBranchAccessPolicy()

__all__ = ["BranchAccessError", "ServerBranchAccessPolicy", "branch_access_policy"]
