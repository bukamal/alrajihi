#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 212 guard: startup/runtime stabilization checks.

This guard is intentionally headless.  CI environments often do not provide
PyQt5, so it installs a minimal PyQt5 shim before importing service-layer code.
It catches the class of regressions that recently appeared at application
startup: circular imports, broken lazy exports, migration SQL errors, and gateway
factory objects that do not implement the common ``is_remote()`` contract.
"""
from __future__ import annotations

import ast
import os
import shutil
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
RUNTIME = Path(os.environ.get("ALRAJHI_PHASE212_RUNTIME", "/tmp/alrajhi_phase212_runtime"))


def _install_pyqt_stub() -> None:
    try:
        import PyQt5  # noqa: F401
        return
    except Exception:
        pass

    settings_store = {"network/mode": "local"}

    class QSettings:
        def __init__(self, *args, **kwargs):
            pass

        def value(self, key, default=None, *args, **kwargs):
            return settings_store.get(key, default)

        def setValue(self, key, value):
            settings_store[key] = value

        def remove(self, key):
            settings_store.pop(key, None)

    class QObject:
        pass

    class QTimer:
        @staticmethod
        def singleShot(*args, **kwargs):
            return None

    class Qt:
        RightToLeft = 1
        LeftToRight = 0
        AlignRight = 0x0002
        AlignVCenter = 0x0080

    class QSize:
        def __init__(self, *args):
            pass

    class QUrl:
        pass

    def pyqtSignal(*args, **kwargs):
        class Signal:
            def connect(self, *args, **kwargs):
                return None

            def emit(self, *args, **kwargs):
                return None

        return Signal()

    class Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            def _method(*args, **kwargs):
                return None

            return _method

    qtcore = types.ModuleType("PyQt5.QtCore")
    for name, obj in {
        "QSettings": QSettings,
        "QObject": QObject,
        "QTimer": QTimer,
        "Qt": Qt,
        "QSize": QSize,
        "QUrl": QUrl,
        "pyqtSignal": pyqtSignal,
    }.items():
        setattr(qtcore, name, obj)

    qtwidgets = types.ModuleType("PyQt5.QtWidgets")
    for name in (
        "QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout "
        "QHBoxLayout QLabel QPushButton QLineEdit QTableWidget "
        "QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit "
        "QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog "
        "QInputDialog QProgressDialog QFrame QSplitter QScrollArea"
    ).split():
        setattr(qtwidgets, name, Dummy)

    qtgui = types.ModuleType("PyQt5.QtGui")
    for name in "QIcon QPixmap QFont QColor QDesktopServices".split():
        setattr(qtgui, name, Dummy)

    pyqt = types.ModuleType("PyQt5")
    pyqt.QtCore = qtcore
    pyqt.QtWidgets = qtwidgets
    pyqt.QtGui = qtgui
    sys.modules.update(
        {
            "PyQt5": pyqt,
            "PyQt5.QtCore": qtcore,
            "PyQt5.QtWidgets": qtwidgets,
            "PyQt5.QtGui": qtgui,
        }
    )


def _prepare_runtime() -> None:
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    os.environ["ALRAJHI_DATA_DIR"] = str(RUNTIME)
    os.environ["ALRAJHI_DB_PATH"] = str(RUNTIME / "phase212_runtime.db")


def _check_local_gateway_contracts() -> list[str]:
    missing: list[str] = []
    for path in sorted((CLIENT / "gateways" / "local").glob("*gateway.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Local") and node.name.endswith("Gateway"):
                methods = {m.name for m in node.body if isinstance(m, ast.FunctionDef)}
                if "is_remote" not in methods:
                    missing.append(f"{path.relative_to(ROOT)}:{node.name}")
    return missing


def _import_core_services() -> int:
    count = 0
    for path in sorted((CLIENT / "core" / "services").glob("*service.py")):
        __import__("core.services." + path.stem)
        count += 1
    return count


def _instantiate_gateway_factories() -> int:
    count = 0
    for path in sorted((CLIENT / "gateways").glob("*gateway.py")):
        module = __import__("gateways." + path.stem, fromlist=["*"])
        for name, obj in vars(module).items():
            if not (name.startswith("create_") and callable(obj)):
                continue
            instance = obj()
            gateways = instance if isinstance(instance, tuple) else (instance,)
            for gateway in gateways:
                if not hasattr(gateway, "is_remote"):
                    raise AssertionError(f"{type(gateway).__name__} from {name} lacks is_remote()")
                remote_value = gateway.is_remote()
                if not isinstance(remote_value, bool):
                    raise AssertionError(f"{type(gateway).__name__}.is_remote() must return bool")
            count += 1
    return count


def _check_database_bootstrap() -> str:
    from database.migrations import init_database

    init_database()
    db_path = Path(os.environ["ALRAJHI_DB_PATH"])
    if not db_path.exists():
        raise AssertionError(f"Expected database to be created at {db_path}")
    return str(db_path)


def _check_dashboard_expense_contract() -> None:
    from database import expense_dao

    if not hasattr(expense_dao, "get_all"):
        raise AssertionError("database.expense_dao must export DAO object with get_all(), not module")


def main() -> int:
    _prepare_runtime()
    _install_pyqt_stub()
    sys.path.insert(0, str(CLIENT))
    sys.path.insert(0, str(ROOT))

    missing = _check_local_gateway_contracts()
    if missing:
        raise AssertionError("Local gateways missing is_remote(): " + ", ".join(missing))

    db_path = _check_database_bootstrap()
    service_count = _import_core_services()
    factory_count = _instantiate_gateway_factories()
    _check_dashboard_expense_contract()

    print(
        "phase212_runtime_stabilization_guard: OK "
        f"db={db_path} services={service_count} gateway_factories={factory_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
