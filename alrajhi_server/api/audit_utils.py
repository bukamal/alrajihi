# -*- coding: utf-8 -*-
import json
import datetime
from flask import request
from flask_jwt_extended import get_jwt_identity
from alrajhi_server.repositories.audit_event_repository import AuditEventRepository


def _json(value):
    try:
        return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
    except Exception:
        return str(value)


def audit_log(action, entity_type, entity_id=None, old_values=None, new_values=None, details='', source='API',
              audit_scope='', permission_key='', branch_id=None, event_category=''):
    try:
        repo = AuditEventRepository()
        user_id = None
        username = 'api'
        try:
            user_id = get_jwt_identity()
            if user_id:
                username = repo.get_username(user_id) or username
        except Exception:
            pass
        now = datetime.datetime.now().isoformat(timespec='seconds')
        detail_payload = details
        if old_values is not None or new_values is not None:
            detail_payload = _json({'details': details, 'old': old_values, 'new': new_values})
        repo.insert_audit_log({
            'user_id': user_id, 'username': username, 'action': action,
            'table_name': entity_type, 'record_id': entity_id, 'details': detail_payload,
            'ip_address': request.remote_addr if request else '', 'timestamp': now,
            'event_time': now, 'entity_type': entity_type, 'entity_id': entity_id,
            'old_values': _json(old_values) if old_values is not None else None,
            'new_values': _json(new_values) if new_values is not None else None,
            'session_id': '', 'source': source,
            'audit_scope': audit_scope, 'permission_key': permission_key,
            'branch_id': branch_id, 'event_category': event_category,
        })
    except Exception:
        pass
