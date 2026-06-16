# -*- coding: utf-8 -*-
"""Runtime permission policy driven by SettingsService.

Phase 146 introduces a lightweight policy layer so operational screens can ask
one stable question (can/cannot) instead of reading scattered settings keys.
It is intentionally conservative: admin is always allowed, unknown roles are
restricted by the configured global policy.
"""
from __future__ import annotations

from typing import Dict, Iterable

from auth.session import UserSession
from core.services.settings_service import settings_service
from core.services.rbac_service import rbac_service


class PermissionService:
    ACTION_HIDE_PROFIT = 'hide_profit'
    ACTION_DELETE = 'delete_records'
    ACTION_EDIT_INVOICES = 'edit_invoices'
    ACTION_EDIT_RETURNS = 'edit_returns'
    ACTION_VIEW_REPORTS = 'view_reports'
    ACTION_EXPORT_REPORTS = 'export_reports'
    ACTION_VIEW_ALL_BRANCHES = 'view_all_branches'
    ACTION_MANAGE_ALL_BRANCHES = 'manage_all_branches'

    DEFAULTS = {
        ACTION_HIDE_PROFIT: False,
        ACTION_DELETE: True,
        ACTION_EDIT_INVOICES: True,
        ACTION_EDIT_RETURNS: True,
        ACTION_VIEW_REPORTS: True,
        ACTION_EXPORT_REPORTS: True,
        ACTION_VIEW_ALL_BRANCHES: False,
        ACTION_MANAGE_ALL_BRANCHES: False,
    }

    def current_role(self) -> str:
        return (UserSession.get_current_user_role() or 'admin').strip().lower()

    def is_admin(self, role: str | None = None) -> bool:
        return (role or self.current_role()).strip().lower() == 'admin'

    def _blocked_roles(self, key: str) -> set[str]:
        raw = settings_service.get(key, '') or ''
        return {x.strip().lower() for x in str(raw).split(',') if x.strip()}

    def policy(self) -> Dict[str, object]:
        return {
            'hide_profit_for_non_admin': settings_service.get_bool('security/hide_profit_for_non_admin', False),
            'prevent_delete_for_non_admin': settings_service.get_bool('security/prevent_delete_for_non_admin', False),
            'prevent_invoice_edit_for_non_admin': settings_service.get_bool('security/prevent_invoice_edit_for_non_admin', False),
            'prevent_return_edit_for_non_admin': settings_service.get_bool('security/prevent_return_edit_for_non_admin', False),
            'restrict_reports_to_admin': settings_service.get_bool('security/restrict_reports_to_admin', False),
            'restrict_report_export_to_admin': settings_service.get_bool('security/restrict_report_export_to_admin', False),
            'blocked_report_roles': sorted(self._blocked_roles('security/blocked_report_roles')),
            'restrict_branch_scope_for_non_admin': settings_service.get_bool('security/restrict_branch_scope_for_non_admin', True),
            'allow_non_admin_view_all_branches': settings_service.get_bool('security/allow_non_admin_view_all_branches', False),
            'allow_non_admin_manage_all_branches': settings_service.get_bool('security/allow_non_admin_manage_all_branches', False),
        }

    def can(self, action: str, role: str | None = None) -> bool:
        role = (role or self.current_role()).strip().lower()
        allowed = True
        reason = ''
        if self.is_admin(role):
            return True
        try:
            # Phase157: database-backed RBAC overrides coarse legacy settings when available.
            if rbac_service.list_roles():
                mapped = {
                    self.ACTION_DELETE: 'invoices.delete',
                    self.ACTION_EDIT_INVOICES: 'invoices.edit',
                    self.ACTION_EDIT_RETURNS: 'returns.edit',
                    self.ACTION_VIEW_REPORTS: 'reports.view',
                    self.ACTION_EXPORT_REPORTS: 'reports.export',
                    self.ACTION_VIEW_ALL_BRANCHES: 'branches.view_all',
                    self.ACTION_MANAGE_ALL_BRANCHES: 'branches.manage_all',
                }.get(action)
                if mapped:
                    allowed = rbac_service.has_permission(mapped)
                    if not allowed:
                        self.log_event('RBAC_DENIED', action=mapped, allowed=False, reason='rbac_permission_missing', role=role)
                    return allowed
        except Exception:
            pass
        if action == self.ACTION_DELETE and settings_service.get_bool('security/prevent_delete_for_non_admin', False):
            allowed, reason = False, 'prevent_delete_for_non_admin'
        elif action == self.ACTION_EDIT_INVOICES and settings_service.get_bool('security/prevent_invoice_edit_for_non_admin', False):
            allowed, reason = False, 'prevent_invoice_edit_for_non_admin'
        elif action == self.ACTION_EDIT_RETURNS and settings_service.get_bool('security/prevent_return_edit_for_non_admin', False):
            allowed, reason = False, 'prevent_return_edit_for_non_admin'
        elif action == self.ACTION_VIEW_REPORTS:
            if settings_service.get_bool('security/restrict_reports_to_admin', False):
                allowed, reason = False, 'restrict_reports_to_admin'
            elif role in self._blocked_roles('security/blocked_report_roles'):
                allowed, reason = False, 'blocked_report_roles'
        elif action == self.ACTION_EXPORT_REPORTS and settings_service.get_bool('security/restrict_report_export_to_admin', False):
            allowed, reason = False, 'restrict_report_export_to_admin'
        elif action == self.ACTION_VIEW_ALL_BRANCHES:
            if settings_service.get_bool('security/restrict_branch_scope_for_non_admin', True) and not settings_service.get_bool('security/allow_non_admin_view_all_branches', False):
                allowed, reason = False, 'restrict_branch_scope_for_non_admin'
        elif action == self.ACTION_MANAGE_ALL_BRANCHES:
            if not settings_service.get_bool('security/allow_non_admin_manage_all_branches', False):
                allowed, reason = False, 'manage_all_branches_restricted'
        else:
            allowed = self.DEFAULTS.get(action, True)
        if not allowed:
            self.log_event('PERMISSION_DENIED', action=action, allowed=False, reason=reason, role=role)
        return allowed

    def can_view_all_branches(self, role: str | None = None) -> bool:
        role = (role or self.current_role()).strip().lower()
        if self.is_admin(role):
            return True
        try:
            if rbac_service.list_roles():
                return rbac_service.has_permission('branches.view_all')
        except Exception:
            pass
        if not settings_service.get_bool('security/restrict_branch_scope_for_non_admin', True):
            return True
        return settings_service.get_bool('security/allow_non_admin_view_all_branches', False)

    def branch_scope(self) -> dict:
        """Return the effective branch scope for the current user.

        Admins, or users allowed by policy, may see all branches. Other users
        are restricted to their session branch, falling back to the configured
        default branch. This is read-only and safe for reports.
        """
        if self.can_view_all_branches():
            return {'mode': 'all', 'branch_id': None}
        try:
            from core.services.branch_service import branch_service
            return {'mode': 'current', 'branch_id': branch_service.current_branch_id()}
        except Exception:
            return {'mode': 'current', 'branch_id': None}

    def effective_branch_id(self, requested_branch_id=None):
        if requested_branch_id not in (None, '', 0, '0') and self.can_view_all_branches():
            try:
                return int(requested_branch_id)
            except Exception:
                return None
        scope = self.branch_scope()
        return scope.get('branch_id') if scope.get('mode') != 'all' else None

    def should_hide_profit(self, role: str | None = None) -> bool:
        role = (role or self.current_role()).strip().lower()
        return (not self.is_admin(role)) and settings_service.get_bool('security/hide_profit_for_non_admin', False)

    # ========== Security event log (Phase 147) ==========
    def _ensure_security_event_table(self, conn) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                action TEXT,
                role TEXT,
                username TEXT,
                allowed INTEGER NOT NULL DEFAULT 0,
                reason TEXT,
                context TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_time ON security_events(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_action ON security_events(action, role)")

    def log_event(self, event_type: str, action: str = '', allowed: bool = False,
                  reason: str = '', context: str = '', role: str | None = None) -> None:
        """Write a local, non-blocking security event.

        This intentionally never raises to the UI; permission checks must not fail
        just because the audit table is unavailable.
        """
        try:
            from datetime import datetime
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return
            conn = db.get_connection()
            self._ensure_security_event_table(conn)
            username = ''
            try:
                username = UserSession.get_current_username() or ''
            except Exception:
                username = ''
            conn.execute("""
                INSERT INTO security_events(event_type, action, role, username, allowed, reason, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(event_type or 'SECURITY'), str(action or ''), str(role or self.current_role()),
                  str(username or ''), 1 if allowed else 0, str(reason or ''), str(context or ''),
                  datetime.now().isoformat(timespec='seconds')))
            conn.commit()
        except Exception:
            pass

    def security_events(self, limit: int = 200):
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return []
            conn = db.get_connection()
            self._ensure_security_event_table(conn)
            rows = conn.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (int(limit or 200),)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def denied_events_count(self) -> int:
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return 0
            conn = db.get_connection()
            self._ensure_security_event_table(conn)
            return int(conn.execute("SELECT COUNT(*) FROM security_events WHERE allowed=0").fetchone()[0])
        except Exception:
            return 0

    def denied_message(self, action: str) -> str:
        labels = {
            self.ACTION_DELETE: 'الحذف غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EDIT_INVOICES: 'تعديل الفواتير غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EDIT_RETURNS: 'تعديل المرتجعات غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_VIEW_REPORTS: 'عرض التقارير غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EXPORT_REPORTS: 'تصدير التقارير غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_VIEW_ALL_BRANCHES: 'عرض كل الفروع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANAGE_ALL_BRANCHES: 'إدارة كل الفروع غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
        }
        return labels.get(action, 'لا تملك صلاحية تنفيذ هذه العملية.')


permission_service = PermissionService()
