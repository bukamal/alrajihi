# -*- coding: utf-8 -*-
"""Phase 440 audit helpers for project-wide visual identity adoption.

The sweep is intentionally static and conservative.  It does not claim every
legacy widget is pixel-perfect; it identifies local styling debt and ensures new
project-wide runtime polish/Windows acceptance artifacts exist.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import csv
import json
import re
from typing import Iterable

STYLE_CALL_RE = re.compile(r"\.setStyleSheet\s*\(")
STYLE_SOURCES = ("alrajhi_client/views", "alrajhi_client/features", "alrajhi_client/ui")
CENTRAL_STYLE_FILES = {
    "alrajhi_client/theme/qss.py",
    "alrajhi_client/ui/runtime_visual_polish.py",
    "alrajhi_client/views/widgets/modern_ui.py",
}
ALLOWED_LOCAL_STYLE_CONTEXT = (
    "ThemeManager.get",
    "ThemeManager.get_stylesheet",
    "BRAND",
    "visualRole",
    "setProperty",
    "runtime_visual_polish",
)
HIGH_RISK_HARDCODED_COLORS = ("#ff", "#FF", "yellow", "orange", "background: #", "background-color: #")


@dataclass(frozen=True)
class LocalStyleRecord:
    path: str
    line: int
    classification: str
    reason: str
    snippet: str


def _iter_python_files(root: Path) -> Iterable[Path]:
    for rel in STYLE_SOURCES:
        base = root / rel
        if base.exists():
            yield from sorted(base.rglob("*.py"))


def _line_window(lines: list[str], line_no: int, radius: int = 2) -> str:
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return " ".join(line.strip() for line in lines[start - 1:end])[:260]


def scan_local_visual_styles(root: Path) -> list[LocalStyleRecord]:
    records: list[LocalStyleRecord] = []
    for path in _iter_python_files(root):
        rel = path.relative_to(root).as_posix()
        if rel in CENTRAL_STYLE_FILES:
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            continue
        lines = source.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "setStyleSheet"):
                continue
            line = getattr(node, "lineno", 0) or 0
            snippet = _line_window(lines, line)
            has_token = any(marker in snippet for marker in ALLOWED_LOCAL_STYLE_CONTEXT)
            has_hardcoded = any(marker in snippet for marker in HIGH_RISK_HARDCODED_COLORS)
            if rel.endswith("login_dialog.py") or rel.endswith("splash_screen.py"):
                classification = "branded_startup_allowed"
                reason = "startup/login surfaces already have dedicated branded contracts"
            elif has_token and not has_hardcoded:
                classification = "tokenized_local_style"
                reason = "uses ThemeManager/BRAND or runtime visual properties"
            elif has_token and has_hardcoded:
                classification = "mixed_legacy_style"
                reason = "has tokenized style but still includes literal colors/backgrounds"
            else:
                classification = "legacy_local_style"
                reason = "direct local stylesheet should be migrated to central QSS or visualRole"
            records.append(LocalStyleRecord(rel, line, classification, reason, snippet))
    return records


def legacy_visual_style_summary(root: Path) -> dict:
    records = scan_local_visual_styles(root)
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.classification] = counts.get(rec.classification, 0) + 1
    brand = (root / "alrajhi_client/theme/brand.py").read_text(encoding="utf-8")
    qss = (root / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    polish = (root / "alrajhi_client/ui/runtime_visual_polish.py").read_text(encoding="utf-8")
    required = [
        "legacy_visual_style_sweep_phase",
        "windows_runtime_acceptance_phase",
        "visualIdentitySweepPhase",
        "visualStyleSource",
        "QWidget[projectVisualIdentityPhase=\"440\"]",
        "QScrollArea[visualRole=\"workspace_scroll\"]",
        "QSplitter[visualRole=\"workspace_splitter\"]",
    ]
    combined = "\n".join([brand, qss, polish])
    missing = [marker for marker in required if marker not in combined]
    return {
        "ready": not missing,
        "checks": len(required) + len(records),
        "issues": len(missing),
        "details": [f"missing marker: {marker}" for marker in missing],
        "total_local_styles": len(records),
        "counts": counts,
    }


def write_legacy_visual_style_audit(root: Path, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or (root / "tools" / "audit_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    records = scan_local_visual_styles(root)
    csv_path = out_dir / "legacy_visual_style_sweep.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "line", "classification", "reason", "snippet"])
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))
    summary = legacy_visual_style_summary(root)
    summary_path = out_dir / "legacy_visual_style_sweep_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**summary, "csv": str(csv_path), "summary_json": str(summary_path)}


__all__ = [
    "LocalStyleRecord",
    "scan_local_visual_styles",
    "legacy_visual_style_summary",
    "write_legacy_visual_style_audit",
]
