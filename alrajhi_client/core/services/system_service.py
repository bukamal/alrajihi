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
        """Run read-only local SQLite consistency checks behind the SystemGateway."""
        return self._get_gateway().integrity_checks()

    def local_diagnostics_snapshot(self) -> Dict[str, object]:
        """Return read-only local database diagnostics without exposing DatabaseConnection to UI."""
        return self._get_gateway().local_diagnostics_snapshot()


system_service = SystemService()
