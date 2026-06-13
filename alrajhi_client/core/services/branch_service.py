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
                return bid
        except Exception:
            pass
        return self.default_branch_id()

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

    def add_branch(self, data: Dict) -> int:
        branch_id = self.gateway.create(data)
        audit_service.log('CREATE', 'BRANCH', branch_id, new_values=data, details='إنشاء فرع')
        return branch_id

    def update_branch(self, branch_id: int, data: Dict) -> None:
        old = self.branch_by_id(branch_id)
        self.gateway.update(branch_id, data)
        audit_service.log('UPDATE', 'BRANCH', branch_id, old_values=old, new_values=self.branch_by_id(branch_id) or data, details='تعديل فرع')

    def archive_branch(self, branch_id: int) -> None:
        old = self.branch_by_id(branch_id)
        self.gateway.archive(branch_id)
        audit_service.log('SOFT_DELETE', 'BRANCH', branch_id, old_values=old, details='أرشفة فرع')


branch_service = BranchService()
