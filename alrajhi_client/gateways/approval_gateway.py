# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ApprovalGateway(ABC):
    @abstractmethod
    def ensure_schema(self, conn=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def ensure_invoice_request(self, invoice: Dict[str, Any], threshold_amount: Any, requested_by: str, notes: str = '') -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def set_invoice_request_status(self, invoice_id: int, status: str, decided_by: str, notes: str = '') -> None:
        raise NotImplementedError

    @abstractmethod
    def pending(self, limit: int = 200) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def ensure_advanced_schema(self, conn=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def matrix_for(self, document_type: str, invoice_type: str | None, amount: Any) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def ensure_steps_for_request(self, approval_request_id: int, document_type: str = 'INVOICE', invoice_type: str | None = None, amount: Any = 0) -> int:
        raise NotImplementedError

    @abstractmethod
    def pending_step(self, approval_request_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def approve_current_step(self, approval_request_id: int, username: str, notes: str = '') -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def request_status(self, approval_request_id: int) -> Dict[str, Any]:
        raise NotImplementedError


def create_approval_gateway() -> ApprovalGateway:
    from gateways.local.approval_gateway import LocalApprovalGateway
    return LocalApprovalGateway()
