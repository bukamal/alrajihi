# -*- coding: utf-8 -*-
"""Application service for runtime/system diagnostics."""
from __future__ import annotations

from typing import Dict, List

from gateways.system_gateway import create_system_gateway


class SystemService:
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            self._gateway = create_system_gateway()
        return self._gateway

    def is_remote(self) -> bool:
        return self._get_gateway().is_remote()

    def mode(self) -> str:
        return self._get_gateway().mode()

    def set_mode(self, mode: str) -> None:
        self._get_gateway().set_mode(mode)

    def server_url(self) -> str:
        return self._get_gateway().server_url()

    def data_source_label(self) -> str:
        return self._get_gateway().data_source_label()

    def logout_remote(self) -> None:
        self._get_gateway().logout_remote()

    def debug_status(self) -> Dict:
        return self._get_gateway().debug_status()

    def request_log(self) -> List[Dict]:
        return self._get_gateway().request_log()


    def ensure_local_database(self) -> None:
        self._get_gateway().ensure_local_database()

    def ensure_server_database(self) -> None:
        self._get_gateway().ensure_server_database()

    def configure_server_database_path(self) -> str:
        return self._get_gateway().configure_server_database_path()

    def default_port(self) -> int:
        return self._get_gateway().default_port()

    def get_server_port(self) -> int:
        return self._get_gateway().get_server_port()

    def normalize_server_url(self, address=None, port=None, default_scheme: str = "http") -> str:
        return self._get_gateway().normalize_server_url(address, port, default_scheme)

    def server_diagnostics(self, url=None, timeout: float = 3.0, require_routes: bool = True):
        return self._get_gateway().server_diagnostics(url, timeout=timeout, require_routes=require_routes)

    def health_check(self, url=None, timeout: float = 2.0, require_routes: bool = True) -> bool:
        return self._get_gateway().health_check(url, timeout=timeout, require_routes=require_routes)

    def port_in_use(self, port: int, host: str = "127.0.0.1") -> bool:
        return self._get_gateway().port_in_use(port, host=host)

    def start_server_process(self, main_file=None, port=None):
        return self._get_gateway().start_server_process(main_file=main_file, port=port)

    def stop_server_process(self):
        return self._get_gateway().stop_server_process()

    def restart_server_process(self, main_file=None, port=None):
        return self._get_gateway().restart_server_process(main_file=main_file, port=port)

    def server_status(self):
        return self._get_gateway().server_status()

    def get_server_runtime_info(self):
        return self._get_gateway().get_server_runtime_info()

    def open_server_data_dir(self):
        return self._get_gateway().open_server_data_dir()

    def backup_server_database(self):
        return self._get_gateway().backup_server_database()

    def integrity_checks(self) -> Dict[str, object]:
        """Run local SQLite consistency checks used by the Settings diagnostics tab.

        This method is intentionally read-only. It reports operational risks; it
        does not mutate stock, invoices, BOMs, or orphaned rows.
        """
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return {'mode': 'remote', 'checks': [], 'summary': 'Remote diagnostics are limited to server debug status.'}
            conn = db.get_connection()
            checks = []
            def scalar(sql, params=()):
                try:
                    return conn.execute(sql, params).fetchone()[0]
                except Exception as exc:
                    return f'ERROR: {exc}'
            checks.append({'code': 'negative_items_stock', 'label': 'مواد بمخزون سالب', 'value': scalar("SELECT COUNT(*) FROM items WHERE CAST(COALESCE(quantity,'0') AS REAL) < 0")})
            checks.append({'code': 'negative_warehouse_stock', 'label': 'أرصدة مستودعات سالبة', 'value': scalar("SELECT COUNT(*) FROM item_warehouse_balances WHERE CAST(COALESCE(quantity,'0') AS REAL) < 0")})
            checks.append({'code': 'invoices_without_lines', 'label': 'فواتير بلا أسطر', 'value': scalar("SELECT COUNT(*) FROM (SELECT i.id FROM invoices i LEFT JOIN invoice_lines l ON l.invoice_id=i.id WHERE i.deleted_at IS NULL GROUP BY i.id HAVING COUNT(l.id)=0)")})
            checks.append({'code': 'orphan_invoice_lines', 'label': 'أسطر فواتير بلا فاتورة', 'value': scalar("SELECT COUNT(*) FROM invoice_lines l LEFT JOIN invoices i ON i.id=l.invoice_id WHERE i.id IS NULL")})
            checks.append({'code': 'missing_invoice_customers', 'label': 'فواتير بيع بعميل مفقود', 'value': scalar("SELECT COUNT(*) FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id WHERE i.type='sale' AND i.customer_id IS NOT NULL AND c.id IS NULL")})
            checks.append({'code': 'missing_invoice_suppliers', 'label': 'فواتير شراء بمورد مفقود', 'value': scalar("SELECT COUNT(*) FROM invoices i LEFT JOIN suppliers s ON s.id=i.supplier_id WHERE i.type='purchase' AND i.supplier_id IS NOT NULL AND s.id IS NULL")})
            checks.append({'code': 'broken_bom_components', 'label': 'مكونات BOM مكسورة', 'value': scalar("SELECT COUNT(*) FROM bom_components bc LEFT JOIN items i ON i.id=bc.component_item_id WHERE i.id IS NULL")})
            checks.append({'code': 'settings_audit_rows', 'label': 'سجل تغييرات الإعدادات', 'value': scalar("SELECT COUNT(*) FROM settings_audit")})
            checks.append({'code': 'security_denied_events', 'label': 'عمليات مرفوضة بالصلاحيات', 'value': scalar("SELECT COUNT(*) FROM security_events WHERE allowed=0")})
            try:
                checks.append({'code': 'approval_pending_count', 'label': 'طلبات اعتماد معلقة', 'value': scalar("SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'")})
                checks.append({'code': 'journal_entries_count', 'label': 'القيود اليومية', 'value': scalar("SELECT COUNT(*) FROM journal_entries")})
                checks.append({'code': 'unposted_accounting_invoices', 'label': 'فواتير مرحلة بلا قيد محاسبي', 'value': scalar("SELECT COUNT(*) FROM invoices i WHERE COALESCE(i.workflow_status,'DRAFT')='POSTED' AND i.deleted_at IS NULL AND NOT EXISTS (SELECT 1 FROM journal_entries j WHERE j.source_type='INVOICE' AND j.source_id=i.id)")})
            except Exception:
                pass

            checks.append({'code': 'branches_count', 'label': 'عدد الفروع النشطة', 'value': scalar("SELECT COUNT(*) FROM branches WHERE deleted_at IS NULL AND COALESCE(is_active,1)=1")})
            try:
                from core.services.branch_service import branch_service
                scope = branch_service.report_scope()
                checks.append({'code': 'branch_report_scope', 'label': 'نطاق تقارير الفروع', 'value': f"{scope.get('mode')}:{scope.get('branch_name') or scope.get('branch_id') or 'all'}"})
            except Exception as exc:
                checks.append({'code': 'branch_report_scope', 'label': 'نطاق تقارير الفروع', 'value': f'ERROR: {exc}'})
            checks.append({'code': 'warehouses_without_branch', 'label': 'مستودعات بلا فرع', 'value': scalar("SELECT COUNT(*) FROM warehouses WHERE deleted_at IS NULL AND branch_id IS NULL")})
            checks.append({'code': 'invoices_without_branch', 'label': 'فواتير بلا فرع', 'value': scalar("SELECT COUNT(*) FROM invoices WHERE deleted_at IS NULL AND branch_id IS NULL")})
            checks.append({'code': 'returns_without_branch', 'label': 'مرتجعات بلا فرع', 'value': scalar("SELECT (SELECT COUNT(*) FROM sales_returns WHERE branch_id IS NULL) + (SELECT COUNT(*) FROM purchase_returns WHERE branch_id IS NULL)")})
            try:
                from core.services.workflow_policy_service import workflow_policy_service
                workflow_policy_service.ensure_schema()
                wf = workflow_policy_service.diagnostics()
                checks.append({'code': 'workflow_draft_invoices', 'label': 'فواتير مسودة', 'value': wf.get('draft', 0)})
                checks.append({'code': 'workflow_pending_approvals', 'label': 'فواتير بانتظار الاعتماد', 'value': wf.get('submitted', 0)})
                checks.append({'code': 'workflow_approved_invoices', 'label': 'فواتير معتمدة غير مرحلة', 'value': wf.get('approved', 0)})
                checks.append({'code': 'workflow_cancelled_invoices', 'label': 'فواتير ملغاة', 'value': wf.get('cancelled', 0)})
                checks.append({'code': 'workflow_deleted_invoices', 'label': 'فواتير محذوفة Soft Delete', 'value': wf.get('deleted', 0)})
            except Exception as exc:
                checks.append({'code': 'workflow_diagnostics', 'label': 'تشخيص سير العمل', 'value': f'ERROR: {exc}'})

            quick = scalar('PRAGMA quick_check')
            checks.append({'code': 'sqlite_quick_check', 'label': 'SQLite quick_check', 'value': quick})
            risk_count = 0
            for c in checks:
                v = c.get('value')
                if isinstance(v, (int, float)) and v > 0 and c.get('code') not in ('settings_audit_rows', 'branches_count'):
                    risk_count += int(v)
                elif isinstance(v, str) and v not in ('ok', '0') and c.get('code') == 'sqlite_quick_check':
                    risk_count += 1
            return {'mode': 'local', 'risk_count': risk_count, 'checks': checks}
        except Exception as exc:
            return {'mode': 'error', 'error': str(exc), 'checks': []}


system_service = SystemService()
