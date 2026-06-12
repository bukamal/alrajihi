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
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict

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
    configured = str(settings.value("network/server_url", "") or "").strip()
    return normalize_server_url(configured, get_server_port())



def normalize_server_url(address: Optional[str] = None, port: Optional[int] = None, default_scheme: str = "http") -> str:
    """Normalize server address entered by the user.

    Accepts all common forms:
      - 10.98.199.132 + 8000
      - 10.98.199.132:8000
      - http://10.98.199.132:8000
      - http://10.98.199.132/health
      - http://10.98.199.132:8000/api/routes

    Returns a clean base URL like: http://10.98.199.132:8000
    """
    from urllib.parse import urlparse, urlunparse

    raw = str(address or "").strip()
    port = _to_int(port or DEFAULT_PORT, DEFAULT_PORT)

    if not raw:
        raw = f"localhost:{port}"

    # Fix common user typo: http//host -> http://host
    if raw.startswith("http//"):
        raw = "http://" + raw[len("http//"):]
    elif raw.startswith("https//"):
        raw = "https://" + raw[len("https//"):]

    # If no scheme is present, add one so urlparse handles host:port correctly.
    if "://" not in raw:
        raw = f"{default_scheme}://{raw}"

    parsed = urlparse(raw)
    scheme = parsed.scheme or default_scheme
    host = parsed.hostname or parsed.path.strip("/")
    if not host:
        host = "localhost"

    final_port = parsed.port or port

    # Keep IPv6 brackets if needed.
    netloc_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    netloc = f"{netloc_host}:{final_port}"

    return urlunparse((scheme, netloc, "", "", "", "")).rstrip("/")


def server_diagnostics(url: Optional[str] = None, timeout: float = 3.0, require_routes: bool = True) -> Tuple[bool, str, dict]:
    """Return detailed connectivity diagnostics instead of a bare True/False.

    The function is intentionally authentication-free: it probes only public
    endpoints (/health and /api/routes), so it can be used before login, from the
    network settings dialog, and during troubleshooting.  Authenticated database
    diagnostics are handled separately through RestClient.debug_status().
    """
    base_url = normalize_server_url(url or get_server_url(), get_server_port())
    info = {
        "url": base_url,
        "health": None,
        "routes": None,
        "missing_routes": [],
        "latency_ms": None,
        "api_version": None,
        "route_count": 0,
    }
    try:
        started = time.perf_counter()
        resp = requests.get(f"{base_url}/health", timeout=timeout)
        info["latency_ms"] = int((time.perf_counter() - started) * 1000)
        info["health"] = {"status_code": resp.status_code, "text": resp.text[:500]}
        if resp.status_code != 200:
            return False, f"الخادم أجاب لكن /health أعاد الحالة {resp.status_code}.", info
        try:
            payload = resp.json()
        except Exception:
            return False, "الخادم أجاب على /health لكن الرد ليس JSON صالحاً.", info
        info["api_version"] = payload.get("api_version")
        if payload.get("status") != "alive":
            return False, f"الخادم أجاب لكن الحالة ليست alive: {payload}", info
        if not require_routes:
            return True, "الخادم يعمل ويجيب على /health.", info

        routes_started = time.perf_counter()
        routes_resp = requests.get(f"{base_url}/api/routes", timeout=timeout)
        info["routes_latency_ms"] = int((time.perf_counter() - routes_started) * 1000)
        info["routes"] = {"status_code": routes_resp.status_code, "text": routes_resp.text[:2000]}
        if routes_resp.status_code != 200:
            return False, (
                "الخادم يعمل، لكن مسار /api/routes غير متاح. "
                "هذا يعني غالباً أن نسخة الخادم أقدم من العميل أو أن عنوان العميل يشير إلى خادم آخر."
            ), info
        try:
            routes_payload = routes_resp.json()
        except Exception:
            return False, "مسار /api/routes أجاب لكن الرد ليس JSON صالحاً.", info
        routes = set(routes_payload.get("routes", []))
        info["route_count"] = len(routes)
        info["api_version"] = routes_payload.get("api_version", info.get("api_version"))
        normalized_routes = set(routes)
        normalized_routes.update(r.replace('<path:key>', '<key>') for r in routes)
        missing = sorted(REQUIRED_REMOTE_ROUTES - normalized_routes)
        info["missing_routes"] = missing
        if missing:
            return False, "الخادم يعمل لكن توجد مسارات API ناقصة: " + ", ".join(missing), info
        return True, "الاتصال ناجح والخادم متوافق مع هذه النسخة.", info
    except requests.exceptions.ConnectTimeout:
        return False, f"انتهت مهلة الاتصال بالخادم: {base_url}", info
    except requests.exceptions.ConnectionError as exc:
        return False, f"تعذر فتح اتصال بالخادم: {base_url}\n{exc}", info
    except Exception as exc:
        return False, f"فشل اختبار الاتصال: {exc}", info


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, int(port))) == 0
    except Exception:
        return False


# Routes that must exist on the server for remote/client mode.
# Important: do not require protected concrete URLs such as
# /api/settings/theme here.  The settings endpoint is intentionally
# protected and returns 401 without a token; /api/routes exposes it as
# /api/settings/<key>, which is enough to prove the API exists.
REQUIRED_REMOTE_ROUTES = {
    '/api/reports/summary',
    '/api/settings/<key>',
    '/api/users',
    '/api/cashboxes',
    '/api/returns/sales',
    '/api/manufacturing/boms',
    '/api/debug/status',
}

def health_check(url: Optional[str] = None, timeout: float = 2.0, require_routes: bool = True) -> bool:
    ok, _message, _info = server_diagnostics(url, timeout=timeout, require_routes=require_routes)
    return ok


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
    settings.remove("server/started_at")
    settings.sync()


def _get_writable_paths() -> Tuple[Path, Path]:
    """Return (db_path, backup_dir) for the server-side SQLite data.

    This is safe in source mode and PyInstaller builds.  It must never point to
    Program Files or _internal for writable data.
    """
    try:
        from alrajhi_server.database.paths import get_server_db_path, ensure_data_dir
        db_path = Path(get_server_db_path()).expanduser()
        data_dir = Path(ensure_data_dir()).expanduser()
    except Exception:
        try:
            from core.app_paths import local_db_path, backups_dir
            db_path = Path(local_db_path()).expanduser()
            data_dir = Path(backups_dir()).expanduser().parent
        except Exception:
            if os.name == "nt":
                base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Local")) / "AlrajhiAccounting"
            else:
                base = Path.home() / ".alrajhi"
            db_path = base / "alrajhi_data.db"
            data_dir = base
    backup_dir = data_dir / "server_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path, backup_dir


def get_server_runtime_info() -> Dict[str, object]:
    """Return safe server status information for the settings UI."""
    settings = QSettings("Alrajhi", "Accounting")
    port = get_server_port()
    pid = get_saved_pid()
    running, message = server_status()
    db_path, backup_dir = _get_writable_paths()
    started_at = str(settings.value("server/started_at", "") or "")
    uptime = "-"
    if started_at:
        try:
            started_ts = float(started_at)
            seconds = max(0, int(time.time() - started_ts))
            h, rem = divmod(seconds, 3600)
            m, s = divmod(rem, 60)
            uptime = f"{h:02d}:{m:02d}:{s:02d}"
        except Exception:
            uptime = "-"
    return {
        "running": running,
        "message": message,
        "pid": pid or "-",
        "pid_running": is_pid_running(pid) if pid else False,
        "port": port,
        "uptime": uptime,
        "db_path": str(db_path),
        "backup_dir": str(backup_dir),
        "auto_start": settings.value("server/auto_start", False, type=bool),
    }


def open_server_data_dir() -> Tuple[bool, str]:
    db_path, _backup_dir = _get_writable_paths()
    folder = db_path.parent
    folder.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, f"تم فتح مجلد بيانات الخادم:\n{folder}"
    except Exception as exc:
        return False, f"تعذر فتح مجلد البيانات:\n{folder}\n{exc}"


def backup_server_database() -> Tuple[bool, str]:
    """Create a safe SQLite backup of the server database."""
    db_path, backup_dir = _get_writable_paths()
    if not db_path.exists():
        return False, f"لا توجد قاعدة بيانات للخادم في المسار:\n{db_path}"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"alrajhi_server_backup_{stamp}.db"
    try:
        src = sqlite3.connect(str(db_path))
        try:
            dst = sqlite3.connect(str(target))
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        return True, f"تم إنشاء نسخة احتياطية لقاعدة الخادم:\n{target}"
    except Exception as exc:
        try:
            shutil.copy2(str(db_path), str(target))
            return True, f"تم نسخ قاعدة الخادم احتياطياً بطريقة مباشرة:\n{target}"
        except Exception as copy_exc:
            return False, f"فشل النسخ الاحتياطي لقاعدة الخادم:\n{exc}\n{copy_exc}"


def restart_server_process(main_file: Optional[str] = None, port: Optional[int] = None) -> Tuple[bool, str]:
    stopped, stop_msg = stop_server_process()
    if not stopped:
        return False, stop_msg
    time.sleep(0.8)
    started, start_msg = start_server_process(main_file=main_file, port=port or get_server_port())
    return started, (stop_msg + "\n" + start_msg)


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
        settings.setValue("server/started_at", str(time.time()))
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
