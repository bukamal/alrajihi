# -*- coding: utf-8 -*-
"""Application service for pending offline write operations."""
from __future__ import annotations

from typing import Dict, List

from gateways.offline_queue_gateway import create_offline_queue_gateway


class OfflineQueueService:
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            self._gateway = create_offline_queue_gateway()
        return self._gateway

    def recent(self, limit: int = 300) -> List[Dict]:
        return self._get_gateway().recent(limit)

    def count_pending(self) -> int:
        return self._get_gateway().count_pending()

    def delete(self, req_id: int) -> None:
        self._get_gateway().delete(req_id)

    def clear_sent(self) -> None:
        self._get_gateway().clear_sent()

    def process_pending(self) -> Dict[str, int]:
        return self._get_gateway().process_pending()


offline_queue_service = OfflineQueueService()
