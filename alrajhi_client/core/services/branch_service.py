# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional

from core.services.audit_service import audit_service
from gateways.branch_gateway import create_branch_gateway


class BranchService:
    def __init__(self):
        self.gateway = create_branch_gateway()

    def bootstrap(self) -> None:
        self.gateway.bootstrap()

    def branches(self, include_archived: bool = False) -> List[Dict]:
        return self.gateway.list(include_archived=include_archived)

    def branch_by_id(self, branch_id: int) -> Optional[Dict]:
        return self.gateway.get(branch_id)

    def default_branch_id(self) -> int | None:
        # Phase 149: settings may pin a runtime default branch.  If the setting
        # is invalid or the branch was archived, fall back to the repository
        # default so old databases continue to work.
        try:
            from core.services.settings_service import settings_service
            configured = settings_service.get('branches/default_branch_id', '')
            if configured not in (None, '', '0', 0):
                branch = self.branch_by_id(int(configured))
                if branch and not branch.get('deleted_at') and int(branch.get('is_active') or 1) == 1:
                    return int(branch['id'])
        except Exception:
            pass
        try:
            return self.gateway.default_branch_id()
        except Exception:
            # In remote/client mode this may fail while offline.  Creating a
            # queueable document must not crash just because the default branch
            # could not be fetched; the server can resolve/validate branch_id
            # when the queued request is replayed.
            return None

    def default_branch(self) -> Optional[Dict]:
        bid = self.default_branch_id()
        return self.branch_by_id(bid) if bid else None

    def current_branch_id(self) -> int | None:
        try:
            from auth.session import UserSession
            bid = UserSession.get_current_branch_id()
            if bid:
                try:
                    from workspace.branches.branch_access_policy import branch_access_policy
                    if branch_access_policy.can_access_branch(bid):
                        return int(bid)
                    allowed = branch_access_policy.allowed_branch_ids()
                    if allowed:
                        return int(allowed[0])
                except Exception:
                    return int(bid)
        except Exception:
            pass
        default_id = self.default_branch_id()
        try:
            from workspace.branches.branch_access_policy import branch_access_policy
            if default_id and branch_access_policy.can_access_branch(default_id):
                return int(default_id)
            allowed = branch_access_policy.allowed_branch_ids()
            if allowed:
                return int(allowed[0])
        except Exception:
            pass
        return default_id

    def can_access_branch(self, branch_id) -> bool:
        try:
            from workspace.branches.branch_access_policy import branch_access_policy
            return branch_access_policy.can_access_branch(branch_id)
        except Exception:
            return True

    def require_branch_access(self, branch_id, *, context: str = '') -> int | None:
        from workspace.branches.branch_access_policy import branch_access_policy
        return branch_access_policy.require_branch_access(branch_id, context=context)

    def scoped_query_params(self, requested_branch_id=None) -> Dict:
        try:
            from workspace.branches.branch_access_policy import branch_access_policy
            return branch_access_policy.scope_query_params(requested_branch_id)
        except Exception:
            return {}

    def report_scope(self, requested_branch_id=None) -> Dict:
        """Return branch visibility scope used by reports and diagnostics.

        When the permission policy restricts non-admin users to their branch, a
        requested branch is ignored unless the user may view all branches.
        """
        try:
            from core.services.permission_service import permission_service
            bid = permission_service.effective_branch_id(requested_branch_id)
            if bid:
                return {'mode': 'branch', 'branch_id': int(bid), 'branch_name': self.branch_name(int(bid))}
            if permission_service.can_view_all_branches():
                return {'mode': 'all', 'branch_id': None, 'branch_name': 'كل الفروع'}
        except Exception:
            pass
        bid = self.current_branch_id()
        return {'mode': 'branch', 'branch_id': bid, 'branch_name': self.branch_name(bid) if bid else ''}

    def warehouses_for_scope(self, branch_id=None) -> List[int]:
        """Return warehouse IDs visible in the effective branch scope."""
        scope = self.report_scope(branch_id)
        if scope.get('mode') == 'all':
            return []
        bid = scope.get('branch_id')
        if not bid:
            return []
        try:
            from core.services.warehouse_service import warehouse_service
            return [int(w.get('id')) for w in warehouse_service.warehouses(include_archived=False)
                    if int(w.get('branch_id') or 0) == int(bid)]
        except Exception:
            return []

    def ensure_branch_id(self, data: Dict | None) -> Dict:
        payload = dict(data or {})
        if not payload.get('branch_id'):
            branch_id = self.current_branch_id()
            if branch_id:
                payload['branch_id'] = branch_id
        return payload

    def branch_name(self, branch_id: int | None) -> str:
        branch = self.branch_by_id(branch_id) if branch_id else self.default_branch()
        return (branch or {}).get('name', '')

    def set_default_branch(self, branch_id: int) -> None:
        from core.services.branch_operation_policy import branch_operation_policy
        branch_operation_policy.require(branch_operation_policy.OP_SET_DEFAULT, context='BranchService.set_default_branch', payload={'branch_id': branch_id})
        old = self.default_branch()
        self.gateway.set_default(int(branch_id))
        try:
            from core.services.settings_service import settings_service
            settings_service.set('branches/default_branch_id', str(int(branch_id)))
        except Exception:
            pass
        audit_service.log('UPDATE', 'BRANCH_DEFAULT', branch_id, old_values=old, new_values=self.branch_by_id(branch_id), details='تغيير الفرع الافتراضي')

    def diagnostics(self) -> Dict:
        try:
            return self.gateway.diagnostics()
        except Exception as exc:
            return {'mode': 'error', 'error': str(exc), 'checks': []}

    def add_branch(self, data: Dict) -> int:
        from core.services.branch_operation_policy import branch_operation_policy
        branch_operation_policy.require(branch_operation_policy.OP_CREATE, context='BranchService.add_branch', payload=data)
        branch_id = self.gateway.create(data)
        audit_service.log('CREATE', 'BRANCH', branch_id, new_values=data, details='إنشاء فرع')
        return branch_id

    def update_branch(self, branch_id: int, data: Dict) -> None:
        from core.services.branch_operation_policy import branch_operation_policy
        branch_operation_policy.require(branch_operation_policy.OP_EDIT, context='BranchService.update_branch', payload={'branch_id': branch_id, 'data': data})
        old = self.branch_by_id(branch_id)
        self.gateway.update(branch_id, data)
        audit_service.log('UPDATE', 'BRANCH', branch_id, old_values=old, new_values=self.branch_by_id(branch_id) or data, details='تعديل فرع')

    def archive_branch(self, branch_id: int) -> None:
        from core.services.branch_operation_policy import branch_operation_policy
        branch_operation_policy.require(branch_operation_policy.OP_ARCHIVE, context='BranchService.archive_branch', payload={'branch_id': branch_id})
        old = self.branch_by_id(branch_id)
        self.gateway.archive(branch_id)
        audit_service.log('SOFT_DELETE', 'BRANCH', branch_id, old_values=old, details='أرشفة فرع')


branch_service = BranchService()
