# -*- coding: utf-8 -*-
"""System/runtime gateway contract.

Phase 15 keeps UI code away from DatabaseConnection and REST request-log
internals.  Runtime diagnostics and remote logout belong behind this gateway.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class SystemGateway(ABC):
    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def mode(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def set_mode(self, mode: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def server_url(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def data_source_label(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def logout_remote(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def debug_status(self) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def request_log(self) -> List[Dict]:
        raise NotImplementedError


    @abstractmethod
    def ensure_local_database(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def ensure_server_database(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def configure_server_database_path(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def default_port(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_server_port(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def normalize_server_url(self, address=None, port=None, default_scheme: str = "http") -> str:
        raise NotImplementedError

    @abstractmethod
    def server_diagnostics(self, url=None, timeout: float = 3.0, require_routes: bool = True):
        raise NotImplementedError

    @abstractmethod
    def health_check(self, url=None, timeout: float = 2.0, require_routes: bool = True) -> bool:
        raise NotImplementedError

    @abstractmethod
    def port_in_use(self, port: int, host: str = "127.0.0.1") -> bool:
        raise NotImplementedError

    @abstractmethod
    def start_server_process(self, main_file=None, port=None):
        raise NotImplementedError

    @abstractmethod
    def stop_server_process(self):
        raise NotImplementedError

    @abstractmethod
    def restart_server_process(self, main_file=None, port=None):
        raise NotImplementedError

    @abstractmethod
    def server_status(self):
        raise NotImplementedError

    @abstractmethod
    def get_server_runtime_info(self):
        raise NotImplementedError

    @abstractmethod
    def open_server_data_dir(self):
        raise NotImplementedError

    @abstractmethod
    def backup_server_database(self):
        raise NotImplementedError


def create_system_gateway() -> SystemGateway:
    # The gateway factory is the allowed boundary for DatabaseConnection.
    from gateways.local.system_gateway import LocalSystemGateway
    return LocalSystemGateway()
