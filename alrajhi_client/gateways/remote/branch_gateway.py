# -*- coding: utf-8 -*-
"""Remote API branch gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from gateways.branch_gateway import BranchGateway


class RemoteBranchGateway(BranchGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def bootstrap(self) -> None:
        # Defaults are server-side responsibility in remote mode.
        return None

    def list(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return self.rest_client.get_branches(include_archived=include_archived)

    def get(self, branch_id: int) -> Optional[Dict[str, Any]]:
        branch = self.rest_client.get_branch(branch_id)
        return branch if isinstance(branch, dict) else None

    def default_branch_id(self) -> int | None:
        return self.rest_client.default_branch_id()

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_branch(data)

    def update(self, branch_id: int, data: Dict[str, Any]):
        return self.rest_client.update_branch(branch_id, data)

    def archive(self, branch_id: int):
        return self.rest_client.archive_branch(branch_id)

    def set_default(self, branch_id: int):
        raise NotImplementedError('تعيين الفرع الافتراضي يتطلب Route في الخادم')

    def diagnostics(self):
        return {'mode': 'remote', 'checks': []}

    def is_remote(self) -> bool:
        return True
