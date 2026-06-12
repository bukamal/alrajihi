# -*- coding: utf-8 -*-
"""Utilities for controlling the optional embedded Alrajhi server.

The desktop client must not restart itself repeatedly just because the saved
network mode is "server".  These helpers keep server lifecycle explicit:
settings decide whether the server should auto-start, while the settings screen
can start/stop it manually.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from typing import Optional, Tuple

import requests
from PyQt5.QtCore import QSettings

DEFAULT_PORT = 8000


def _to_int(value, default: int = DEFAULT_PORT) -> int:
    try:
        return int(value)
    except Exception:
        return default


def get_server_port() -> int:
    settings = QSettings("Alrajhi", "Accounting")
    return _to_int(settings.value("server/port", DEFAULT_PORT), DEFAULT_PORT)


def get_server_url() -> str:
    settings = QSettings("Alrajhi", "Accounting")
    configured = str(settings.value("network/server_url", "") or "").strip().rstrip("/")
    if configured:
        return configured
    return f"http://localhost:{get_server_port()}"


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, int(port))) == 0
    except Exception:
        return False


REQUIRED_REMOTE_ROUTES = {
    '/api/reports/summary',
    '/api/settings/theme',
    '/api/users',
    '/api/cashboxes',
    '/api/returns/sales',
    '/api/manufacturing/boms',
}

def health_check(url: Optional[str] = None, timeout: float = 2.0, require_routes: bool = True) -> bool:
    url = (url or get_server_url()).rstrip("/")
    try:
        resp = requests.get(f"{url}/health", timeout=timeout)
        if resp.status_code != 200 or resp.json().get("status") != "alive":
            return False
        if not require_routes:
            return True
        routes_resp = requests.get(f"{url}/api/routes", timeout=timeout)
        if routes_resp.status_code != 200:
            return False
        routes = set(routes_resp.json().get('routes', []))
        # Flask routes may include variable parts; exact static API roots must exist.
        return REQUIRED_REMOTE_ROUTES.issubset(routes)
    except Exception:
        return False


def is_pid_running(pid: int) -> bool:
    if not pid:
        return False
    try:
        if os.name == "nt":
            # tasklist returns 0 even for headers; search exact PID in output.
            out = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], text=True, stderr=subprocess.DEVNULL)
            return str(pid) in out
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def get_saved_pid() -> int:
    settings = QSettings("Alrajhi", "Accounting")
    return _to_int(settings.value("server/pid", 0), 0)


def clear_saved_pid() -> None:
    settings = QSettings("Alrajhi", "Accounting")
    settings.remove("server/pid")
    settings.sync()


def server_status() -> Tuple[bool, str]:
    port = get_server_port()
    pid = get_saved_pid()
    if health_check(f"http://127.0.0.1:{port}", timeout=1.0):
        return True, f"الخادم يعمل على المنفذ {port}."
    if port_in_use(port):
        return True, f"المنفذ {port} مشغول بخدمة أخرى أو خادم يعمل مسبقاً."
    if pid and not is_pid_running(pid):
        clear_saved_pid()
    return False, f"الخادم متوقف على المنفذ {port}."


def start_server_process(main_file: Optional[str] = None, port: Optional[int] = None, wait_seconds: int = 8) -> Tuple[bool, str]:
    """Start the embedded server once.

    Returns (success, message). It never opens another GUI client; the child is
    launched with --server and ALRAJHI_SERVER_CHILD=1.
    """
    settings = QSettings("Alrajhi", "Accounting")
    port = _to_int(port or settings.value("server/port", DEFAULT_PORT), DEFAULT_PORT)

    if port_in_use(port):
        if health_check(f"http://127.0.0.1:{port}", timeout=1.0):
            return True, f"الخادم يعمل مسبقاً على المنفذ {port}."
        return False, f"المنفذ {port} مشغول ولا يمكن تشغيل الخادم عليه."

    main_file = main_file or os.path.abspath(sys.argv[0])
    env = os.environ.copy()
    env["ALRAJHI_SERVER_CHILD"] = "1"
    env["ALRAJHI_SERVER_PORT"] = str(port)

    # In source mode: python main.py --server. In frozen mode: app.exe --server.
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--server"]
    else:
        cmd = [sys.executable, os.path.abspath(main_file), "--server"]

    try:
        kwargs = {"env": env}
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.Popen(cmd, **kwargs)
        settings.setValue("server/pid", int(proc.pid))
        settings.setValue("server/port", int(port))
        # Keep local URL coherent when this machine is the server.
        if settings.value("network/mode", "local") == "server":
            settings.setValue("network/server_url", f"http://localhost:{port}")
        settings.sync()
    except Exception as exc:
        return False, f"فشل تشغيل الخادم: {exc}"

    deadline = time.time() + max(1, wait_seconds)
    while time.time() < deadline:
        if health_check(f"http://127.0.0.1:{port}", timeout=1.0):
            return True, f"تم تشغيل الخادم على المنفذ {port}."
        time.sleep(0.4)
    return False, f"تم طلب تشغيل الخادم لكن لم يستجب خلال {wait_seconds} ثوانٍ."


def stop_server_process() -> Tuple[bool, str]:
    port = get_server_port()
    pid = get_saved_pid()
    if not pid:
        if port_in_use(port):
            return False, "الخادم أو خدمة أخرى تعمل على المنفذ، لكن لا يوجد PID محفوظ لإيقافه بأمان."
        return True, "الخادم متوقف بالفعل."

    if not is_pid_running(pid):
        clear_saved_pid()
        return True, "الخادم متوقف بالفعل."

    try:
        if os.name == "nt":
            subprocess.call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(int(pid), 15)
            time.sleep(1)
            if is_pid_running(pid):
                os.kill(int(pid), 9)
        clear_saved_pid()
        return True, "تم إيقاف الخادم."
    except Exception as exc:
        return False, f"فشل إيقاف الخادم: {exc}"
