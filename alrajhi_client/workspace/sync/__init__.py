# -*- coding: utf-8 -*-
from .offline_sync_contract import (
    OfflineDecision,
    OfflineSyncDescriptor,
    offline_decision_for_api,
    offline_descriptor_for,
    offline_sync_descriptors,
    offline_sync_matrix,
    queueable_api_prefixes,
    queueable_descriptors,
    validate_offline_sync_descriptors,
)

__all__ = [
    "OfflineDecision",
    "OfflineSyncDescriptor",
    "offline_decision_for_api",
    "offline_descriptor_for",
    "offline_sync_descriptors",
    "offline_sync_matrix",
    "queueable_api_prefixes",
    "queueable_descriptors",
    "validate_offline_sync_descriptors",
]

from .replay_safety import (
    REPLAY_STATUS_CONFLICT,
    REPLAY_STATUS_FAILED,
    REPLAY_STATUS_RETRY,
    build_idempotency_key,
    classify_replay_error,
    replay_headers,
)

__all__ += [
    "REPLAY_STATUS_CONFLICT",
    "REPLAY_STATUS_FAILED",
    "REPLAY_STATUS_RETRY",
    "build_idempotency_key",
    "classify_replay_error",
    "replay_headers",
]
