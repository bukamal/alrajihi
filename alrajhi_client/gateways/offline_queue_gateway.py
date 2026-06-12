# -*- coding: utf-8 -*-
"""Offline queue gateway contract and factory."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class OfflineQueueGateway(ABC):
    @abstractmethod
    def recent(self, limit: int = 300) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def count_pending(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete(self, req_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_sent(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_pending(self) -> Dict[str, int]:
        raise NotImplementedError


def create_offline_queue_gateway() -> OfflineQueueGateway:
    from gateways.local.offline_queue_gateway import LocalOfflineQueueGateway
    return LocalOfflineQueueGateway()
