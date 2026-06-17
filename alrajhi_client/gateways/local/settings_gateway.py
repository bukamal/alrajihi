# -*- coding: utf-8 -*-
"""Local settings gateway adapter."""
from __future__ import annotations

from typing import Any, Dict

from database.repositories.settings_repo import SettingsRepository
from gateways.settings_gateway import SettingsGateway
from core.services.audit_service import audit_service


class LocalSettingsGateway(SettingsGateway):
    def __init__(self):
        self.repo = SettingsRepository()

    def is_remote(self) -> bool:
        return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.repo.get(key, default)

    def set(self, key: str, value: str) -> None:
        self.repo.set(key, value)

    def clear_cache(self) -> None:
        self.repo.clear_cache()

    def get_language(self) -> str:
        return self.repo.get_language()

    def get_theme(self) -> str:
        return self.repo.get_theme()

    def get_currency_settings(self) -> Dict[str, Any]:
        return self.repo.get_currency_settings()

    def audit_rows(self, limit: int = 100):
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return []
            conn = db.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL, old_value TEXT, new_value TEXT,
                    changed_by TEXT, changed_at TEXT NOT NULL, source TEXT DEFAULT 'SettingsService'
                )
            """)
            rows = conn.execute("SELECT * FROM settings_audit ORDER BY id DESC LIMIT ?", (int(limit or 100),)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
    def export_settings_dict(self) -> Dict[str, Any]:
        """Return all local settings as a dictionary for support/backup purposes."""
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return {}
            conn = db.get_connection()
            rows = conn.execute('SELECT key, value, category, updated_at FROM settings ORDER BY key').fetchall()
            return {row['key']: {'value': row['value'], 'category': row['category'], 'updated_at': row['updated_at']} for row in rows}
        except Exception:
            return {}

    def import_settings_dict(self, payload: Dict[str, Any]) -> int:
        """Import settings exported by export_settings_dict. Returns changed row count."""
        count = 0
        for key, item in dict(payload or {}).items():
            if not key:
                continue
            value = item.get('value') if isinstance(item, dict) else item
            self.set(str(key), '' if value is None else str(value))
            count += 1
        self.clear_cache()
        audit_service.log('IMPORT', 'SETTINGS', None, details=f'استيراد إعدادات ({count})')
        return count
    def _profile_conn(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        if db.is_remote():
            return None
        conn = db.get_connection()
        now_sql = "datetime('now')"
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings_profile_values (
                profile_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                updated_at TEXT,
                PRIMARY KEY (profile_id, setting_key),
                FOREIGN KEY(profile_id) REFERENCES settings_profiles(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_settings_profile_values_key ON settings_profile_values(setting_key)")
        conn.execute("""
            INSERT OR IGNORE INTO settings_profiles(id, name, description, is_active, created_at, updated_at)
            VALUES (1, 'Default', 'ملف الإعدادات الافتراضي', 1, datetime('now'), datetime('now'))
        """)
        active_count = conn.execute("SELECT COUNT(*) FROM settings_profiles WHERE is_active=1").fetchone()[0]
        if not active_count:
            conn.execute("UPDATE settings_profiles SET is_active=1 WHERE id=(SELECT MIN(id) FROM settings_profiles)")
        conn.commit()
        return conn

    def profile_value(self, key: str, default: Any = None) -> Any:
        try:
            conn = self._profile_conn()
            if conn is None:
                return default
            row = conn.execute("SELECT id FROM settings_profiles WHERE is_active=1 LIMIT 1").fetchone()
            if not row:
                return default
            profile_id = int(row['id'])
            if profile_id == 1:
                return default
            val = conn.execute(
                "SELECT setting_value FROM settings_profile_values WHERE profile_id=? AND setting_key=?",
                (profile_id, key),
            ).fetchone()
            return val['setting_value'] if val else default
        except Exception:
            return default

    def list_profiles(self):
        try:
            conn = self._profile_conn()
            if conn is None:
                return []
            rows = conn.execute("""
                SELECT p.*, COUNT(v.setting_key) AS settings_count
                FROM settings_profiles p
                LEFT JOIN settings_profile_values v ON v.profile_id = p.id
                GROUP BY p.id
                ORDER BY p.is_active DESC, p.id ASC
            """).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_active_profile(self) -> Dict[str, Any]:
        try:
            conn = self._profile_conn()
            if conn is None:
                return {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}
            row = conn.execute("""
                SELECT p.*, COUNT(v.setting_key) AS settings_count
                FROM settings_profiles p
                LEFT JOIN settings_profile_values v ON v.profile_id = p.id
                WHERE p.is_active=1
                GROUP BY p.id
                LIMIT 1
            """).fetchone()
            return dict(row) if row else {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}
        except Exception:
            return {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}

    def create_profile(self, name: str, description: str = '') -> int:
        name = str(name or '').strip()
        if not name:
            raise ValueError('Profile name is required')
        conn = self._profile_conn()
        if conn is None:
            raise RuntimeError('Profiles are available in local mode only')
        now = __import__('datetime').datetime.now().isoformat(timespec='seconds')
        cur = conn.execute(
            "INSERT INTO settings_profiles(name, description, is_active, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
            (name, description or '', now, now),
        )
        conn.commit()
        audit_service.log('CREATE', 'SETTINGS_PROFILE', cur.lastrowid, details=f'إنشاء ملف إعدادات: {name}')
        return int(cur.lastrowid)

    def set_active_profile(self, profile_id: int):
        conn = self._profile_conn()
        if conn is None:
            return
        profile_id = int(profile_id)
        row = conn.execute("SELECT id, name FROM settings_profiles WHERE id=?", (profile_id,)).fetchone()
        if not row:
            raise ValueError('Profile not found')
        old = self.get_active_profile()
        conn.execute("UPDATE settings_profiles SET is_active=0")
        conn.execute("UPDATE settings_profiles SET is_active=1, updated_at=datetime('now') WHERE id=?", (profile_id,))
        conn.commit()
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_PROFILE_ACTIVE', profile_id, old_values=old, new_values=dict(row), details=f'تفعيل ملف إعدادات: {row["name"]}')

    def set_profile_value(self, profile_id: int, key: str, value: Any):
        conn = self._profile_conn()
        if conn is None:
            return
        conn.execute("""
            INSERT OR REPLACE INTO settings_profile_values(profile_id, setting_key, setting_value, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (int(profile_id), str(key), '' if value is None else str(value)))
        conn.commit()

    def log_profile_setting_change(self, profile_id: int, profile_name: str, key: str, old_value: Any, new_value: Any):
        try:
            conn = self._profile_conn()
            if conn is None or str(old_value) == str(new_value):
                return
            now = __import__('datetime').datetime.now().isoformat(timespec='seconds')
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL, old_value TEXT, new_value TEXT,
                    changed_by TEXT, changed_at TEXT NOT NULL, source TEXT DEFAULT 'SettingsService'
                )
            """)
            conn.execute("""
                INSERT INTO settings_audit(setting_key, old_value, new_value, changed_by, changed_at, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f'profile:{profile_name}:{key}', old_value, new_value, None, now, 'SettingsProfile'))
            conn.commit()
        except Exception:
            pass

    def clone_profile(self, source_profile_id: int, new_name: str) -> int:
        source_profile_id = int(source_profile_id or 1)
        conn = self._profile_conn()
        if conn is None:
            raise RuntimeError('Profiles are available in local mode only')
        src = conn.execute("SELECT * FROM settings_profiles WHERE id=?", (source_profile_id,)).fetchone()
        if not src:
            raise ValueError('Source profile not found')
        new_id = self.create_profile(new_name, f"نسخة من {src['name']}")
        rows = conn.execute("SELECT setting_key, setting_value FROM settings_profile_values WHERE profile_id=?", (source_profile_id,)).fetchall()
        if not rows:
            rows = conn.execute("SELECT key AS setting_key, value AS setting_value FROM settings").fetchall()
        for row in rows:
            self.set_profile_value(new_id, row['setting_key'], row['setting_value'])
        audit_service.log('CREATE', 'SETTINGS_PROFILE_CLONE', new_id, details=f'نسخ ملف إعدادات من {src["name"]} إلى {new_name}')
        return new_id

    def export_profile_dict(self, profile_id: int | None = None) -> Dict[str, Any]:
        conn = self._profile_conn()
        if conn is None:
            return {}
        if profile_id is None:
            profile_id = int(self.get_active_profile().get('id') or 1)
        profile = conn.execute("SELECT * FROM settings_profiles WHERE id=?", (int(profile_id),)).fetchone()
        if not profile:
            return {}
        values = conn.execute("SELECT setting_key, setting_value FROM settings_profile_values WHERE profile_id=? ORDER BY setting_key", (int(profile_id),)).fetchall()
        if not values:
            values = conn.execute("SELECT key AS setting_key, value AS setting_value FROM settings ORDER BY key").fetchall()
        return {
            'profile': {k: profile[k] for k in profile.keys()},
            'settings': {r['setting_key']: r['setting_value'] for r in values},
        }

    def import_profile_dict(self, payload: Dict[str, Any]) -> int:
        payload = dict(payload or {})
        profile_data = dict(payload.get('profile') or {})
        settings = dict(payload.get('settings') or {})
        name = str(profile_data.get('name') or 'Imported Profile').strip()
        base = name
        conn = self._profile_conn()
        if conn is None:
            raise RuntimeError('Profiles are available in local mode only')
        i = 1
        while conn.execute("SELECT 1 FROM settings_profiles WHERE name=?", (name,)).fetchone():
            i += 1
            name = f'{base} ({i})'
        profile_id = self.create_profile(name, profile_data.get('description') or 'Imported profile')
        for key, value in settings.items():
            self.set_profile_value(profile_id, key, value)
        audit_service.log('IMPORT', 'SETTINGS_PROFILE', profile_id, details=f'استيراد ملف إعدادات: {name}')
        return profile_id

    def profile_health(self) -> Dict[str, Any]:
        active = self.get_active_profile()
        required = [
            'company/name', 'invoice/sales_prefix', 'invoice/purchase_prefix',
            'inventory/allow_negative_stock', 'units/quantity_decimals',
            'units/price_decimals', 'language', 'language/print', 'language/report',
            'backup/enabled', 'security/prevent_delete_for_non_admin'
        ]
        missing = []
        try:
            conn = self._profile_conn()
            if conn is not None:
                for key in required:
                    has_global = conn.execute('SELECT 1 FROM settings WHERE key=?', (key,)).fetchone() is not None
                    has_profile = conn.execute('SELECT 1 FROM settings_profile_values WHERE profile_id=? AND setting_key=?', (int(active.get('id') or 1), key)).fetchone() is not None
                    if not has_global and not has_profile:
                        missing.append(key)
        except Exception:
            pass
        return {'active_profile': active, 'missing_settings': missing, 'missing_count': len(missing)}

