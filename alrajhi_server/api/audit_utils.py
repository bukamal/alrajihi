# -*- coding: utf-8 -*-
import json
import datetime
from flask import request
from flask_jwt_extended import get_jwt_identity
from database.connection import get_db


def _json(value):
    try:
        return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
    except Exception:
        return str(value)


def _columns(db):
    try:
        return {row[1] for row in db.execute('PRAGMA table_info(audit_log)').fetchall()}
    except Exception:
        return set()


def audit_log(action, entity_type, entity_id=None, old_values=None, new_values=None, details='', source='API'):
    try:
        db = get_db()
        cols = _columns(db)
        user_id = None
        username = 'api'
        try:
            user_id = get_jwt_identity()
            if user_id:
                row = db.execute('SELECT username FROM users WHERE id=?', (user_id,)).fetchone()
                if row:
                    username = row['username']
        except Exception:
            pass
        now = datetime.datetime.now().isoformat(timespec='seconds')
        detail_payload = details
        if old_values is not None or new_values is not None:
            detail_payload = _json({'details': details, 'old': old_values, 'new': new_values})
        data = {
            'user_id': user_id, 'username': username, 'action': action,
            'table_name': entity_type, 'record_id': entity_id, 'details': detail_payload,
            'ip_address': request.remote_addr if request else '', 'timestamp': now,
            'event_time': now, 'entity_type': entity_type, 'entity_id': entity_id,
            'old_values': _json(old_values) if old_values is not None else None,
            'new_values': _json(new_values) if new_values is not None else None,
            'session_id': '', 'source': source,
        }
        insert_cols = [c for c in data if c in cols]
        if insert_cols:
            db.execute(f"INSERT INTO audit_log ({', '.join(insert_cols)}) VALUES ({', '.join(['?']*len(insert_cols))})", tuple(data[c] for c in insert_cols))
    except Exception:
        pass
