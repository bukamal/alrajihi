# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


class BranchAccessDenied(PermissionError):
    """Raised when a user tries to operate on a branch outside his scope."""


def _to_int(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        return int(value)
    except Exception:
        return None


class BranchAccessPolicy:
    """Runtime branch-scope helper used by client services and widgets.

    The class intentionally imports heavy services lazily to avoid circular
    imports at startup and to remain safe in PyInstaller analysis.  It is a thin
    binder over RBAC/user_branch_access and does not replace server-side checks.
    """

    def can_view_all_branches(self) -> bool:
        try:
            from core.services.permission_service import permission_service
            return bool(permission_service.can_view_all_branches())
        except Exception:
            try:
                from core.services.rbac_service import rbac_service
                return bool(rbac_service.has_permission("branches.view_all"))
            except Exception:
                return False

    def allowed_branch_ids(self) -> list[int]:
        try:
            from core.services.rbac_service import rbac_service
            return [int(x) for x in rbac_service.allowed_branch_ids()]
        except Exception:
            return []

    def current_branch_id(self) -> int | None:
        try:
            from core.services.branch_service import branch_service
            return _to_int(branch_service.current_branch_id())
        except Exception:
            return None

    def can_access_branch(self, branch_id: Any) -> bool:
        bid = _to_int(branch_id)
        if bid is None:
            return True
        if self.can_view_all_branches():
            return True
        allowed = set(self.allowed_branch_ids())
        if allowed:
            return bid in allowed
        return bid == self.current_branch_id()

    def effective_branch_id(self, requested_branch_id: Any = None) -> int | None:
        requested = _to_int(requested_branch_id)
        if requested is not None and self.can_view_all_branches():
            return requested
        if requested is not None and self.can_access_branch(requested):
            return requested
        allowed = self.allowed_branch_ids()
        if allowed and not self.can_view_all_branches():
            return int(allowed[0])
        return self.current_branch_id()

    def require_branch_access(self, branch_id: Any, *, context: str = "") -> int | None:
        bid = _to_int(branch_id)
        if bid is not None and not self.can_access_branch(bid):
            suffix = f" in {context}" if context else ""
            raise BranchAccessDenied(f"Branch access denied for branch_id={bid}{suffix}")
        return bid

    def ensure_payload_branch(self, payload: Mapping[str, Any] | None, *, required: bool = True, context: str = "") -> dict[str, Any]:
        data = dict(payload or {})
        bid = _to_int(data.get("branch_id"))
        if bid is None:
            bid = self.effective_branch_id(None)
            if bid is not None:
                data["branch_id"] = bid
        if required and bid is None:
            raise BranchAccessDenied(f"Missing required branch_id{(' in ' + context) if context else ''}")
        if bid is not None:
            self.require_branch_access(bid, context=context)
        return data

    def scope_query_params(self, requested_branch_id: Any = None) -> dict[str, Any]:
        """Return query params suitable for REST/list/report calls.

        Admin/all-branch users may pass no branch_id to request all branches;
        restricted users always get their effective branch_id.
        """
        if self.can_view_all_branches() and _to_int(requested_branch_id) is None:
            return {}
        bid = self.effective_branch_id(requested_branch_id)
        return {"branch_id": bid} if bid is not None else {}

    def filter_records(self, records: Sequence[Mapping[str, Any]], *, branch_key: str = "branch_id") -> list[Mapping[str, Any]]:
        if self.can_view_all_branches():
            return list(records)
        allowed = set(self.allowed_branch_ids())
        current = self.current_branch_id()
        if current is not None:
            allowed.add(current)
        if not allowed:
            return list(records)
        result: list[Mapping[str, Any]] = []
        for row in records:
            bid = _to_int(row.get(branch_key))
            if bid is None or bid in allowed:
                result.append(row)
        return result


branch_access_policy = BranchAccessPolicy()

__all__ = ["BranchAccessDenied", "BranchAccessPolicy", "branch_access_policy"]
