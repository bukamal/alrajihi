# -*- coding: utf-8 -*-
"""Phase 83 hardcoded UI string audit.

This guard intentionally audits remaining human-facing literals after the core
localization phases. It is not a strict zero-literal gate yet because many
remaining Arabic literals are data values, seed data, migration labels, SQL
messages, or report samples.  The generated artifacts are used to drive the
next cleanup phase safely.
"""
from __future__ import annotations

import ast
import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "language_audit"
AR_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
SKIP_DIRS = {"__pycache__", ".git", "build", "dist", "venv", ".venv"}
SKIP_FILES = {
    "alrajhi_client/i18n/translator.py",  # the translation catalog itself
}

UI_HINTS = (
    "views/", "printing/", "action_handler.py", "main.py", "theme_manager.py",
)
DATA_HINTS = (
    "database/", "migrations", "repositories/", "dao/", "models/",
)
SERVER_HINTS = ("alrajhi_server/",)

@dataclass
class Finding:
    file: str
    line: int
    category: str
    language_hint: str
    text: str


def classify(path: str) -> str:
    p = path.replace("\\", "/")
    if any(h in p for h in UI_HINTS):
        return "ui_candidate"
    if any(h in p for h in DATA_HINTS):
        return "data_or_schema_candidate"
    if any(h in p for h in SERVER_HINTS):
        return "api_server_candidate"
    if p.startswith("tools/"):
        return "tooling_candidate"
    return "misc_candidate"


def language_hint(text: str) -> str:
    has_ar = bool(AR_RE.search(text))
    has_lat = bool(LATIN_RE.search(text))
    if has_ar and has_lat:
        return "mixed_ar_latin"
    if has_ar:
        return "arabic"
    if has_lat:
        return "latin"
    return "other"


def should_capture(text: str) -> bool:
    if not text or len(text.strip()) < 2:
        return False
    if text.strip().startswith(("http://", "https://", "sqlite", "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE")):
        return False
    return bool(AR_RE.search(text))


def iter_py_files():
    for p in ROOT.rglob("*.py"):
        rel = p.relative_to(ROOT).as_posix()
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if rel in SKIP_FILES:
            continue
        yield p, rel


def scan() -> list[Finding]:
    findings: list[Finding] = []
    for path, rel in iter_py_files():
        try:
            tree = ast.parse(path.read_text("utf-8"), filename=rel)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value.strip()
                if should_capture(text):
                    findings.append(Finding(rel, getattr(node, "lineno", 0), classify(rel), language_hint(text), text[:240]))
    return findings


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    findings = scan()
    csv_path = OUT_DIR / "hardcoded_arabic_literals.csv"
    json_path = OUT_DIR / "hardcoded_arabic_summary.json"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "line", "category", "language_hint", "text"])
        w.writeheader()
        for item in findings:
            w.writerow(asdict(item))
    summary: dict[str, object] = {"total_findings": len(findings), "by_category": {}, "top_files": []}
    by_cat: dict[str, int] = {}
    by_file: dict[str, int] = {}
    for item in findings:
        by_cat[item.category] = by_cat.get(item.category, 0) + 1
        by_file[item.file] = by_file.get(item.file, 0) + 1
    summary["by_category"] = dict(sorted(by_cat.items()))
    summary["top_files"] = sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:40]
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"hardcoded string audit complete: {len(findings)} findings")
    print(f"csv: {csv_path.relative_to(ROOT)}")
    print(f"json: {json_path.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
