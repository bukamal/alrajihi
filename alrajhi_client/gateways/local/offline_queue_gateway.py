# -*- coding: utf-8 -*-
"""Local offline queue adapter.

The queue is persisted locally even in remote-client mode, so this gateway is
used for both modes.  It hides DatabaseConnection/offline_queue from views.
"""
from __future__ import annotations

import json
from typing import Dict, List

import requests

from database.connection import DatabaseConnection, offline_queue
from workspace.sync.replay_safety import classify_replay_error, replay_headers, REPLAY_STATUS_CONFLICT, REPLAY_STATUS_FAILED
from gateways.offline_queue_gateway import OfflineQueueGateway


class LocalOfflineQueueGateway(OfflineQueueGateway):
    def recent(self, limit: int = 300) -> List[Dict]:
        return offline_queue.get_recent_requests(limit)

    def count_pending(self) -> int:
        return offline_queue.count_pending()

    def delete(self, req_id: int) -> None:
        offline_queue.delete_request(req_id)

    def clear_sent(self) -> None:
        offline_queue.clear_sent()

    def process_pending(self) -> Dict[str, int]:
        db = DatabaseConnection()
        if not db.is_remote():
            return {'sent': 0, 'failed': 0, 'skipped': 1}

        try:
            resp = requests.get(f"{db.server_url}/health", timeout=3)
            if resp.status_code != 200:
                return {'sent': 0, 'failed': 0, 'skipped': 1}
        except Exception:
            return {'sent': 0, 'failed': 0, 'skipped': 1}

        rest = db.get_rest_client()
        if not rest:
            return {'sent': 0, 'failed': 0, 'skipped': 1}

        sent = 0
        failed = 0
        conflicts = 0
        for req in offline_queue.get_pending_requests():
            try:
                offline_queue.mark_replay_locked(req['id'])
                payload = json.loads(req['data']) if req.get('data') else None
                method = (req.get('method') or '').upper()
                headers = replay_headers(req)
                if method == 'POST':
                    rest._request('POST', req['endpoint'], payload, queue_on_failure=False, retries=1, extra_headers=headers)
                elif method == 'PUT':
                    rest._request('PUT', req['endpoint'], payload, queue_on_failure=False, retries=1, extra_headers=headers)
                elif method == 'PATCH':
                    rest._request('PATCH', req['endpoint'], payload, queue_on_failure=False, retries=1, extra_headers=headers)
                elif method == 'DELETE':
                    rest._request('DELETE', req['endpoint'], queue_on_failure=False, retries=1, extra_headers=headers)
                else:
                    offline_queue.mark_replay_unlocked(req['id'])
                    continue
                offline_queue.mark_sent(req['id'])
                sent += 1
                print(f"✅ تم إرسال الطلب المعلق: {req.get('title') or req['endpoint']}")
            except Exception as exc:
                decision = classify_replay_error(exc, req.get('conflict_policy') or '')
                if decision.status == REPLAY_STATUS_CONFLICT:
                    conflicts += 1
                    offline_queue.mark_conflict(req['id'], exc, decision.reason)
                    print(f"🟠 تم وضع الطلب للمراجعة اليدوية {req.get('title') or req['endpoint']}: {exc}")
                elif decision.status == REPLAY_STATUS_FAILED:
                    failed += 1
                    offline_queue.mark_failed(req['id'], exc)
                    print(f"⛔ تم تعليم الطلب المعلق كفاشل نهائياً {req.get('title') or req['endpoint']}: {exc}")
                else:
                    failed += 1
                    offline_queue.mark_attempt(req['id'], exc)
                    offline_queue.mark_replay_unlocked(req['id'])
                    print(f"⚠️ فشل إرسال الطلب المعلق {req.get('title') or req['endpoint']}: {exc}")
        return {'sent': sent, 'failed': failed, 'conflicts': conflicts, 'skipped': 0}

    def is_remote(self) -> bool:
        return False
