# -*- coding: utf-8 -*-
"""Phase 416 runtime acceptance harness.

This module is intentionally import-safe without PyQt.  The real runtime probes
load Qt only inside the functions that need it, so CI/static guards can import
this file on headless machines while a developer machine can run the full Qt
acceptance probes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import csv
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class RuntimeAcceptanceScenario:
    key: str
    surface: str
    mode: str
    objective: str
    expected_evidence: str
    runtime_required: bool = True

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeWidgetSnapshotRow:
    path: str
    class_name: str
    object_name: str
    visible: bool
    enabled: bool
    x: int
    y: int
    width: int
    height: int
    layout_direction: str
    text: str = ""
    role: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


PHASE416_SCENARIOS: tuple[RuntimeAcceptanceScenario, ...] = (
    RuntimeAcceptanceScenario(
        "shell_ar_rtl_snapshot",
        "shell",
        "QWidget tree + screenshot",
        "Open MainWindow in Arabic RTL and capture the full shell widget tree and top navigation screenshot.",
        "Exactly one CleanShellNavigationBar is visible; no ModernTopBar/IconMenuBar/MainNavToolButton remains in the visible tree.",
    ),
    RuntimeAcceptanceScenario(
        "shell_de_ltr_snapshot",
        "shell",
        "QWidget tree + screenshot",
        "Open MainWindow in German/English LTR and capture the shell widget tree after language direction switch.",
        "The top-left paint surface remains owned by CleanShellNavigationBar and has no orphan hidden topbar overlap.",
    ),
    RuntimeAcceptanceScenario(
        "sales_invoice_enter_route",
        "editable_grid",
        "QTest key navigation",
        "Open a sales invoice line grid, type into item/barcode, then press Enter through unit, qty, price, discount, tax, total and notes.",
        "The focus follows the semantic route and never falls back to physical-column traversal.",
    ),
    RuntimeAcceptanceScenario(
        "sales_invoice_shift_enter_route",
        "editable_grid",
        "QTest reverse navigation",
        "Press Shift+Enter from qty/unit/item cells in the sales invoice grid.",
        "The focus returns to the previous semantic editable column without leaving the row unexpectedly.",
    ),
    RuntimeAcceptanceScenario(
        "sales_invoice_value_preservation",
        "editable_grid",
        "QTest editor commit",
        "Place an existing item/unit/qty/price value in the grid, open the editor and press Enter without changing text.",
        "Existing values are preserved; Enter is confirmation/navigation, not a delete operation.",
    ),
    RuntimeAcceptanceScenario(
        "sales_invoice_single_trailing_row",
        "editable_grid",
        "QTest row lifecycle",
        "Press Enter at the end of the last completed sales invoice line several times.",
        "At most one trailing empty line exists after every key press.",
    ),
    RuntimeAcceptanceScenario(
        "sales_invoice_hidden_column_route",
        "editable_grid",
        "QTest column visibility",
        "Hide discount/tax/available columns and press Enter through the sales invoice row.",
        "The route skips hidden columns and does not stop on non-editable columns unless the policy intentionally permits it.",
    ),
    RuntimeAcceptanceScenario(
        "purchase_invoice_enter_route",
        "editable_grid",
        "QTest key navigation",
        "Repeat the semantic Enter route on purchase invoices using cost instead of sales price where applicable.",
        "Purchase invoice traversal follows the same central engine and creates one trailing row only.",
    ),
    RuntimeAcceptanceScenario(
        "returns_enter_route",
        "editable_grid",
        "QTest key navigation",
        "Run Enter navigation on sales and purchase return grids, including reason/restock fields.",
        "Return grids do not use local eventFilter or duplicate dataChanged row append logic.",
    ),
    RuntimeAcceptanceScenario(
        "bom_inventory_enter_route",
        "editable_grid",
        "QTest key navigation",
        "Run Enter navigation on BOM/manufacturing and inventory-transfer editable grids.",
        "BOM and transfer grids use the same row lifecycle gate or are explicitly listed as exceptions.",
    ),
    RuntimeAcceptanceScenario(
        "startup_login_activation_windows",
        "startup",
        "QWidget tree + smoke open",
        "Open splash/login/activation/change-password surfaces and capture object names and geometries.",
        "No overlapping password controls or orphan title-bar widgets appear in RTL/LTR layouts.",
    ),
    RuntimeAcceptanceScenario(
        "settings_preferences_runtime",
        "settings",
        "QSettings persistence smoke",
        "Toggle dashboard privacy and table preference controls, restart the runtime probe, and re-read values.",
        "User preferences persist per user/workstation without mutating company/accounting settings.",
    ),
)


def pyqt_runtime_status() -> dict[str, object]:
    """Return whether a real Qt runtime probe can be executed on this machine."""
    available = importlib.util.find_spec("PyQt5") is not None
    qtest_available = importlib.util.find_spec("PyQt5.QtTest") is not None if available else False
    return {
        "pyqt5_available": available,
        "qttest_available": qtest_available,
        "qt_qpa_platform": os.environ.get("QT_QPA_PLATFORM", ""),
        "runtime_probe_possible": bool(available and qtest_available),
    }


def runtime_acceptance_scenarios() -> tuple[RuntimeAcceptanceScenario, ...]:
    return PHASE416_SCENARIOS


def scenario_matrix_rows() -> list[dict[str, object]]:
    status = pyqt_runtime_status()
    rows: list[dict[str, object]] = []
    for scenario in PHASE416_SCENARIOS:
        row = scenario.as_dict()
        row["pyqt_runtime_status"] = "READY" if status["runtime_probe_possible"] else "NEEDS_LOCAL_QT_RUNTIME"
        rows.append(row)
    return rows


def write_scenario_matrix(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = scenario_matrix_rows()
    fieldnames = [
        "key", "surface", "mode", "objective", "expected_evidence", "runtime_required", "pyqt_runtime_status",
    ]
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


def _safe_text(widget: Any) -> str:
    for attr in ("text", "title", "windowTitle", "toolTip"):
        try:
            value = getattr(widget, attr)()
        except Exception:
            continue
        if value:
            return str(value).replace("\n", " ")[:160]
    return ""


def _safe_property(widget: Any, name: str) -> str:
    try:
        value = widget.property(name)
    except Exception:
        return ""
    return "" if value is None else str(value)


def _layout_direction_name(widget: Any) -> str:
    try:
        value = int(widget.layoutDirection())
    except Exception:
        return "unknown"
    # Qt.LeftToRight == 0, Qt.RightToLeft == 1 in Qt5.
    return "RTL" if value == 1 else "LTR" if value == 0 else str(value)


def _geometry(widget: Any) -> tuple[int, int, int, int]:
    try:
        geo = widget.geometry()
        return int(geo.x()), int(geo.y()), int(geo.width()), int(geo.height())
    except Exception:
        return 0, 0, 0, 0


def collect_widget_tree(root_widget: Any, *, max_depth: int = 12, max_nodes: int = 2500) -> list[RuntimeWidgetSnapshotRow]:
    """Collect a runtime QWidget tree without depending on a specific widget class.

    The result is designed for diagnosing paint/overlap issues such as the
    top-left shell artifact: it records class, objectName, visibility, geometry,
    layout direction and selected role properties for every visible/hidden child.
    """
    rows: list[RuntimeWidgetSnapshotRow] = []

    def walk(widget: Any, parts: list[str], depth: int) -> None:
        if len(rows) >= max_nodes or depth > max_depth:
            return
        class_name = widget.__class__.__name__
        try:
            object_name = str(widget.objectName() or "")
        except Exception:
            object_name = ""
        try:
            visible = bool(widget.isVisible())
        except Exception:
            visible = False
        try:
            enabled = bool(widget.isEnabled())
        except Exception:
            enabled = False
        x, y, w, h = _geometry(widget)
        label = object_name or class_name
        path = "/".join(parts + [label])
        rows.append(RuntimeWidgetSnapshotRow(
            path=path,
            class_name=class_name,
            object_name=object_name,
            visible=visible,
            enabled=enabled,
            x=x,
            y=y,
            width=w,
            height=h,
            layout_direction=_layout_direction_name(widget),
            text=_safe_text(widget),
            role=_safe_property(widget, "shellChromeRole") or _safe_property(widget, "visualWorkspaceType"),
        ))
        try:
            children = list(widget.children())
        except Exception:
            children = []
        for child in children:
            # Layout objects are useful only as parent internals; QWidget/QMenu
            # children are what matter for visible overlap diagnosis.
            if hasattr(child, "geometry") or hasattr(child, "children"):
                walk(child, parts + [label], depth + 1)

    walk(root_widget, [], 0)
    return rows


def write_widget_snapshot(rows: Iterable[RuntimeWidgetSnapshotRow], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(RuntimeWidgetSnapshotRow.__dataclass_fields__.keys())
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())
    return target


def analyze_shell_snapshot(rows: Sequence[RuntimeWidgetSnapshotRow]) -> dict[str, object]:
    """Analyze a shell widget snapshot for known legacy/overlap hazards."""
    clean_shell = [r for r in rows if r.class_name == "CleanShellNavigationBar" or r.object_name == "CleanShellNavigationBar"]
    old_shell = [
        r for r in rows
        if r.class_name in {"ModernTopBar", "IconMenuBar", "QToolButton"}
        or r.object_name in {"ModernTopBar", "IconMenuBar", "MainNavToolButton"}
    ]
    visible_old_shell = [r for r in old_shell if r.visible]
    top_left_candidates = [
        r for r in rows
        if r.visible and r.width > 0 and r.height > 0 and r.x <= 8 and r.y <= 8
        and r.object_name not in {"CleanShellNavigationBar", "centralwidget"}
        and r.class_name not in {"MainWindow", "QWidget", "QHBoxLayout", "QVBoxLayout"}
    ]
    issues: list[str] = []
    if len(clean_shell) != 1:
        issues.append(f"expected exactly one CleanShellNavigationBar, found {len(clean_shell)}")
    if visible_old_shell:
        issues.append("visible legacy shell widgets: " + ", ".join(sorted({r.class_name + ':' + r.object_name for r in visible_old_shell})))
    if top_left_candidates:
        issues.append("top-left overlap candidates: " + ", ".join((r.class_name + ':' + r.object_name) for r in top_left_candidates[:12]))
    return {
        "clean_shell_count": len(clean_shell),
        "old_shell_count": len(old_shell),
        "visible_old_shell_count": len(visible_old_shell),
        "top_left_candidate_count": len(top_left_candidates),
        "issues": issues,
        "ok": not issues,
    }


def _require_pyqt() -> dict[str, Any]:
    if importlib.util.find_spec("PyQt5") is None:
        raise RuntimeError("PyQt5 is not installed; run this probe on the developer/runtime machine.")
    from PyQt5.QtCore import Qt, QTimer  # type: ignore
    from PyQt5.QtTest import QTest  # type: ignore
    from PyQt5.QtWidgets import QApplication  # type: ignore
    return {"Qt": Qt, "QTimer": QTimer, "QTest": QTest, "QApplication": QApplication}


def _app() -> Any:
    qt = _require_pyqt()
    QApplication = qt["QApplication"]
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def run_shell_snapshot_probe(*, language: str = "ar", output_dir: str | Path = "tools/audit_outputs/runtime_acceptance") -> dict[str, object]:
    """Run a real Qt shell snapshot probe on a machine that has PyQt5.

    This probe is deliberately invoked manually; it may open the full MainWindow
    and therefore depends on the local runtime configuration/database.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _app()
    from i18n.translator import set_language  # type: ignore
    from views.main_window import MainWindow  # type: ignore

    set_language(language)
    window = MainWindow()
    try:
        if hasattr(window, "switch_language"):
            window.switch_language(language)
    except Exception:
        pass
    window.resize(1400, 900)
    window.show()
    try:
        _app().processEvents()
    except Exception:
        pass
    rows = collect_widget_tree(window)
    out = Path(output_dir)
    csv_path = write_widget_snapshot(rows, out / f"shell_widget_tree_{language}.csv")
    screenshot_path = out / f"shell_snapshot_{language}.png"
    try:
        out.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(screenshot_path))
    except Exception:
        screenshot_path = Path("")
    analysis = analyze_shell_snapshot(rows)
    payload = {
        "language": language,
        "widget_tree_csv": str(csv_path),
        "screenshot": str(screenshot_path) if screenshot_path else "",
        "analysis": analysis,
    }
    (out / f"shell_snapshot_{language}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        window.close()
    except Exception:
        pass
    return payload


def run_sales_invoice_enter_probe(*, output_dir: str | Path = "tools/audit_outputs/runtime_acceptance") -> dict[str, object]:
    """Run the real QTest sales-invoice Enter smoke probe when PyQt is available."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    qt = _require_pyqt()
    Qt = qt["Qt"]
    QTest = qt["QTest"]
    app = _app()

    from features.transactions.grids.transaction_column_schema import sales_invoice_schema  # type: ignore
    from features.transactions.grids.transaction_line_grid import TransactionLineGrid  # type: ignore
    from features.transactions.grids.transaction_line_model import TransactionLineModel  # type: ignore

    columns = sales_invoice_schema()
    key_to_col = {col.key: i for i, col in enumerate(columns)}
    model = TransactionLineModel(columns, document_type="sales_invoice")
    grid = TransactionLineGrid(columns)
    grid.setModel(model)
    model.add_empty_line()
    model.lines[0].update({"item_id": 101, "item": "Runtime Tea", "unit": "pcs", "qty": 1, "price": 10, "total": 10})
    grid.show()
    app.processEvents()

    first = model.index(0, key_to_col["item"])
    grid.setCurrentIndex(first)
    grid.edit(first)
    app.processEvents()
    value_before = str(model.lines[0].get("item"))
    QTest.keyClick(grid, Qt.Key_Return)
    app.processEvents()
    value_after = str(model.lines[0].get("item"))
    current_key = columns[grid.currentIndex().column()].key if grid.currentIndex().isValid() else ""
    trailing_before = len(model.lines)
    for _ in range(4):
        grid.setCurrentIndex(model.index(0, key_to_col["notes"]))
        QTest.keyClick(grid, Qt.Key_Return)
        app.processEvents()
    trailing_after = len(model.lines)
    trailing_empty = sum(1 for i in range(len(model.lines)) if model.is_empty_line(i))
    result = {
        "value_preserved": value_before == value_after,
        "current_key_after_item_enter": current_key,
        "row_count_before_notes_enter_loop": trailing_before,
        "row_count_after_notes_enter_loop": trailing_after,
        "trailing_empty_count": trailing_empty,
        "ok": value_before == value_after and trailing_empty <= 1,
    }
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sales_invoice_enter_probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        grid.close()
    except Exception:
        pass
    return result


def run_all_available_runtime_probes(*, output_dir: str | Path = "tools/audit_outputs/runtime_acceptance") -> dict[str, object]:
    """Run every probe that is possible on the current machine."""
    status = pyqt_runtime_status()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_scenario_matrix(out / "runtime_acceptance_scenario_matrix.csv")
    payload: dict[str, object] = {"pyqt_status": status, "probes": {}}
    if not status["runtime_probe_possible"]:
        payload["skipped"] = "PyQt5/QtTest is not available on this machine."
        (out / "runtime_acceptance_probe_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    probes: dict[str, object] = {}
    for lang in ("ar", "de"):
        try:
            probes[f"shell_{lang}"] = run_shell_snapshot_probe(language=lang, output_dir=out)
        except Exception as exc:
            probes[f"shell_{lang}"] = {"ok": False, "error": str(exc)}
    try:
        probes["sales_invoice_enter"] = run_sales_invoice_enter_probe(output_dir=out)
    except Exception as exc:
        probes["sales_invoice_enter"] = {"ok": False, "error": str(exc)}
    payload["probes"] = probes
    (out / "runtime_acceptance_probe_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
