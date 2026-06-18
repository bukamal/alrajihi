# -*- coding: utf-8 -*-
"""Scoped table layout and view persistence.

Phase 173 removes the last generic table-layout dependency on raw QSettings.
Every SmartTableView/CustomTableView layout is now saved through
settings_service with a scope that includes user, branch, and active settings
profile.  Header states are binary Qt payloads, so they are serialized as
base64 strings before being stored in the project settings layer.
"""
from __future__ import annotations

import base64
import json
from typing import Any

from PyQt5.QtCore import QByteArray


def _settings_service():
    from core.services.settings_service import settings_service
    return settings_service


def _session_scope() -> tuple[str, str, str]:
    try:
        from auth.session import UserSession
        user_id = str(UserSession.get_current_user_id() or 'anonymous')
        branch_id = str(UserSession.get_current_branch_id() or 'global')
    except Exception:
        user_id, branch_id = 'anonymous', 'global'
    try:
        profile = _settings_service().get_active_profile() or {}
        profile_id = str(profile.get('id') or 1)
    except Exception:
        profile_id = '1'
    return user_id, branch_id, profile_id


def _encode_value(value: Any) -> str:
    if isinstance(value, QByteArray):
        return json.dumps({'__qt_qbytearray__': base64.b64encode(bytes(value)).decode('ascii')}, ensure_ascii=False)
    if isinstance(value, (bytes, bytearray)):
        return json.dumps({'__bytes__': base64.b64encode(bytes(value)).decode('ascii')}, ensure_ascii=False)
    try:
        return json.dumps({'__json__': value}, ensure_ascii=False)
    except TypeError:
        return json.dumps({'__str__': str(value)}, ensure_ascii=False)


def _decode_value(raw: Any, default: Any = None) -> Any:
    if raw in (None, ''):
        return default
    if isinstance(raw, QByteArray):
        return raw
    try:
        payload = json.loads(str(raw))
    except Exception:
        return raw if raw is not None else default
    if not isinstance(payload, dict):
        return payload
    if '__qt_qbytearray__' in payload:
        try:
            return QByteArray(base64.b64decode(payload['__qt_qbytearray__']))
        except Exception:
            return default
    if '__bytes__' in payload:
        try:
            return base64.b64decode(payload['__bytes__'])
        except Exception:
            return default
    if '__json__' in payload:
        return payload.get('__json__')
    if '__str__' in payload:
        return payload.get('__str__')
    return payload


class TablePreferences:
    def __init__(self, namespace='tables'):
        self.namespace = namespace

    def key(self, identity, part):
        safe_identity = str(identity or 'default').strip().replace(' ', '_')
        user_id, branch_id, profile_id = _session_scope()
        return f'ui/{self.namespace}/users/{user_id}/branches/{branch_id}/profiles/{profile_id}/{safe_identity}/{part}'

    def save_state(self, identity, state):
        _settings_service().set(self.key(identity, 'header_state'), _encode_value(state))

    def load_state(self, identity):
        return _decode_value(_settings_service().get(self.key(identity, 'header_state'), None), None)

    def save_value(self, identity, part, value):
        _settings_service().set(self.key(identity, part), _encode_value(value))

    def load_value(self, identity, part, default=None):
        return _decode_value(_settings_service().get(self.key(identity, part), None), default)

    def named_view_key(self, identity, name, part):
        safe_name = str(name or 'default').strip().replace('/', '_')
        return self.key(identity, f'named_views/{safe_name}/{part}')

    def save_named_view(self, identity, name, header_state, filters=None, responsive=True):
        name = str(name or '').strip()
        if not name:
            return
        names = self.named_view_names(identity)
        if name not in names:
            names.append(name)
            self.save_value(identity, 'named_view_names', names)
        _settings_service().set(self.named_view_key(identity, name, 'header_state'), _encode_value(header_state))
        _settings_service().set(self.named_view_key(identity, name, 'filters'), _encode_value(filters or {}))
        _settings_service().set(self.named_view_key(identity, name, 'responsive'), _encode_value(bool(responsive)))

    def load_named_view(self, identity, name):
        name = str(name or '').strip()
        if not name:
            return {}
        return {
            'header_state': _decode_value(_settings_service().get(self.named_view_key(identity, name, 'header_state'), None), None),
            'filters': _decode_value(_settings_service().get(self.named_view_key(identity, name, 'filters'), None), {}) or {},
            'responsive': bool(_decode_value(_settings_service().get(self.named_view_key(identity, name, 'responsive'), None), True)),
        }

    def named_view_names(self, identity):
        names = self.load_value(identity, 'named_view_names', []) or []
        if isinstance(names, str):
            names = [names]
        return [str(n) for n in names if str(n).strip()]

    def reset(self, identity):
        # The settings service does not expose a remove operation for every
        # gateway.  Store empty values instead; loaders treat them as defaults.
        self.save_value(identity, 'header_state', None)
        self.save_value(identity, 'column_filters', {})
