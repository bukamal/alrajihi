# -*- coding: utf-8 -*-
"""Application service helpers used by UI code.

Services are deliberately thin at this stage: they hide legacy DAO return-shape
variance from dialogs/widgets while preserving existing features and APIs.
"""

try:
    from .permission_service import permission_service, PermissionService
except Exception:
    pass

try:
    from .workflow_policy_service import workflow_policy_service, WorkflowPolicyService
except Exception:
    pass

try:
    from .approval_service import approval_service, ApprovalService
except Exception:
    approval_service = None

try:
    from .accounting_service import accounting_service, AccountingService
except Exception:
    accounting_service = None
