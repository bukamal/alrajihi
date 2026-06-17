# -*- coding: utf-8 -*-
"""Workflow gateway contract.

Keeps invoice workflow persistence behind the gateway boundary so services do
not depend on DatabaseConnection or raw SQL.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class WorkflowGateway(ABC):
    @abstractmethod
    def ensure_schema(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def transition_invoice(self, invoice_id: int, new_status: str, action: str, notes: str = '') -> str:
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> Dict[str, Any]:
        raise NotImplementedError


def create_workflow_gateway() -> WorkflowGateway:
    from gateways.local.workflow_gateway import LocalWorkflowGateway
    return LocalWorkflowGateway()
