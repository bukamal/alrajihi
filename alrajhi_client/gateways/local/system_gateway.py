# -*- coding: utf-8 -*-
"""Local runtime gateway implementation."""
from __future__ import annotations

from typing import Dict, List

from database.connection import DatabaseConnection
from gateways.system_gateway import SystemGateway


class LocalSystemGateway(SystemGateway):
    def _db(self) -> DatabaseConnection:
        return DatabaseConnection()

    def is_remote(self) -> bool:
        return self._db().is_remote()

    def mode(self) -> str:
        return getattr(self._db(), 'mode', 'local')

    def set_mode(self, mode: str) -> None:
        self._db().mode = mode

    def server_url(self) -> str:
        return getattr(self._db(), 'server_url', '')

    def data_source_label(self) -> str:
        db = self._db()
        if hasattr(db, 'data_source_label'):
            return db.data_source_label()
        return 'Remote API' if db.is_remote() else 'Local SQLite'

    def logout_remote(self) -> None:
        db = self._db()
        if not db.is_remote():
            return
        rest = db.get_rest_client()
        if rest:
            rest.logout()

    def debug_status(self) -> Dict:
        db = self._db()
        if db.is_remote() and db.get_rest_client():
            status = db.get_rest_client().debug_status()
            status['_mode'] = 'remote'
            return status
        if db.is_remote():
            return {'_mode': 'remote', 'error': 'no_rest_client'}
        return {'_mode': 'local', 'db_path': 'محلي SQLite', 'counts': {}}

    def request_log(self) -> List[Dict]:
        try:
            from database.connection_rest import get_request_log
            return get_request_log()
        except Exception:
            return []


    def ensure_local_database(self) -> None:
        from database import ensure_db
        ensure_db()

    def configure_server_database_path(self) -> str:
        import os
        if os.name == 'nt':
            base = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA') or os.path.expanduser('~\\AppData\\Roaming')
            client_db_path = os.path.join(base, 'Alrajhi', 'alrajhi_data.db')
        else:
            client_db_path = os.path.expanduser('~/.alrajhi/alrajhi_data.db')
        os.environ.setdefault('ALRAJHI_SERVER_DB_PATH', client_db_path)
        return os.environ.get('ALRAJHI_SERVER_DB_PATH', client_db_path)

    def ensure_server_database(self) -> None:
        self.configure_server_database_path()
        from alrajhi_server.database.migrations import ensure_db as ensure_db_remote
        ensure_db_remote()

    def _server_control(self):
        from core import server_control
        return server_control

    def default_port(self) -> int:
        return self._server_control().DEFAULT_PORT

    def get_server_port(self) -> int:
        return self._server_control().get_server_port()

    def normalize_server_url(self, address=None, port=None, default_scheme: str = "http") -> str:
        return self._server_control().normalize_server_url(address, port, default_scheme)

    def server_diagnostics(self, url=None, timeout: float = 3.0, require_routes: bool = True):
        return self._server_control().server_diagnostics(url, timeout=timeout, require_routes=require_routes)

    def health_check(self, url=None, timeout: float = 2.0, require_routes: bool = True) -> bool:
        return self._server_control().health_check(url, timeout=timeout, require_routes=require_routes)

    def port_in_use(self, port: int, host: str = "127.0.0.1") -> bool:
        return self._server_control().port_in_use(port, host=host)

    def start_server_process(self, main_file=None, port=None):
        return self._server_control().start_server_process(main_file=main_file, port=port)

    def stop_server_process(self):
        return self._server_control().stop_server_process()

    def restart_server_process(self, main_file=None, port=None):
        return self._server_control().restart_server_process(main_file=main_file, port=port)

    def server_status(self):
        return self._server_control().server_status()

    def get_server_runtime_info(self):
        return self._server_control().get_server_runtime_info()

    def open_server_data_dir(self):
        return self._server_control().open_server_data_dir()

    def backup_server_database(self):
        return self._server_control().backup_server_database()
