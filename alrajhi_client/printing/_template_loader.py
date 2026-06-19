# -*- coding: utf-8 -*-
"""Runtime-safe access to printing templates.

The Windows frozen build can expose ``alrajhi_client/printing`` as a top-level
``printing`` package.  This loader therefore tries all supported package names
and frozen file locations.  It deliberately does not permanently cache a failed
lookup: a module can become available later during PyInstaller bootstrap, and a
cached fallback would keep producing the weak emergency template that users saw
in browser output.
"""
from __future__ import annotations

import html
import importlib
import importlib.util
import os
import sys
from types import ModuleType
from typing import Any, Callable, Iterable

_TEMPLATE_MODULE_NAMES = (
    ".print_templates",
    "printing.print_templates",
    "alrajhi_client.printing.print_templates",
)

_REAL_MODULE: ModuleType | None = None


def _load_module_from_file(path: str) -> ModuleType | None:
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("printing.print_templates", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Register both names so later absolute/relative imports resolve to the same
    # module in frozen builds.
    sys.modules.setdefault("printing.print_templates", module)
    sys.modules.setdefault("alrajhi_client.printing.print_templates", module)
    return module


def _candidate_template_files() -> Iterable[str]:
    here = os.path.dirname(__file__)
    cwd = os.getcwd()
    frozen_root = getattr(sys, "_MEIPASS", "") or ""
    bases = [here, cwd, frozen_root]
    seen: set[str] = set()
    for base in bases:
        if not base:
            continue
        for rel in (
            "print_templates.py",
            os.path.join("printing", "print_templates.py"),
            os.path.join("alrajhi_client", "printing", "print_templates.py"),
        ):
            path = os.path.abspath(os.path.join(base, rel))
            if path not in seen:
                seen.add(path)
                yield path


def load_print_templates() -> ModuleType | None:
    """Return the real print_templates module when available.

    Successful imports are cached.  Failed imports are not cached so browser
    printing never gets stuck on the emergency renderer after a transient import
    or PyInstaller bootstrap ordering issue.
    """
    global _REAL_MODULE
    if _REAL_MODULE is not None:
        return _REAL_MODULE

    package = __package__ or "printing"
    for name in _TEMPLATE_MODULE_NAMES:
        try:
            module = importlib.import_module(name, package=package) if name.startswith(".") else importlib.import_module(name)
            _REAL_MODULE = module
            return module
        except ModuleNotFoundError as exc:
            # Missing nested dependencies should not permanently break startup;
            # fall through to the next package name / frozen file location.
            continue
        except Exception:
            continue

    for candidate in _candidate_template_files():
        try:
            module = _load_module_from_file(candidate)
            if module is not None:
                _REAL_MODULE = module
                return module
        except Exception:
            continue
    return None


def _html_doc(title: str, body: str) -> str:
    safe_title = html.escape(str(title or ""))
    return (
        "<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'>"
        f"<title>{safe_title}</title>"
        "<style>body{font-family:Tahoma,Arial,sans-serif;margin:24px;direction:rtl;color:#111827;}"
        "h1{font-size:22px;text-align:center;margin:0 0 16px;}"
        "table{width:100%;border-collapse:collapse;margin-top:12px;table-layout:fixed;}"
        "th{background:#1d4ed8;color:white;font-weight:700;}"
        "th,td{border:1px solid #dbe3ef;padding:7px;text-align:center;word-wrap:break-word;}"
        "tr:nth-child(even) td{background:#f8fafc;}"
        ".muted{color:#64748b;text-align:center;margin:8px 0;}"
        "</style></head><body>"
        f"<h1>{safe_title}</h1>{body}</body></html>"
    )


def _fallback_report_template(*args: Any, **kwargs: Any) -> str:
    title = kwargs.get("title") if "title" in kwargs else (args[0] if len(args) > 0 else "تقرير")
    rows = kwargs.get("rows") if "rows" in kwargs else (args[1] if len(args) > 1 else [])
    headers = kwargs.get("headers") if "headers" in kwargs else (args[2] if len(args) > 2 else [])
    subtitle = kwargs.get("subtitle") if "subtitle" in kwargs else (args[3] if len(args) > 3 else "")
    safe_headers = [html.escape(str(h or "")) for h in (headers or [])]
    head = "".join(f"<th>{h}</th>" for h in safe_headers)
    body_rows = []
    for raw in rows or []:
        raw_row = list(raw or [])
        if safe_headers and len(raw_row) < len(safe_headers):
            raw_row += [""] * (len(safe_headers) - len(raw_row))
        cells = "".join(f"<td>{html.escape(str(c or ''))}</td>" for c in raw_row[:len(safe_headers) or None])
        body_rows.append(f"<tr>{cells}</tr>")
    if not body_rows:
        colspan = max(1, len(safe_headers))
        body_rows.append(f"<tr><td colspan='{colspan}'>لا توجد بيانات</td></tr>")
    table = f"<div class='muted'>{html.escape(str(subtitle or ''))}</div><table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
    return _html_doc(str(title or "تقرير"), table)


def _fallback_template(name: str) -> Callable:
    def _render(*args: Any, **kwargs: Any) -> str:
        if name == "report_html":
            return _fallback_report_template(*args, **kwargs)
        title = kwargs.get("title") or kwargs.get("reference") or name.replace("_", " ").title()
        payload = args[0] if args else kwargs
        body = f"<pre style='white-space:pre-wrap;border:1px solid #dbe3ef;padding:12px'>{html.escape(str(payload))}</pre>"
        return _html_doc(str(title), body)
    return _render


def require_template(name: str) -> Callable:
    """Return a late-binding template callable.

    The returned wrapper re-checks the real template module on every call until it
    succeeds.  This prevents module-import timing in frozen builds from locking a
    print button into the emergency renderer for the entire application session.
    """
    fallback = _fallback_template(name)

    def _render(*args: Any, **kwargs: Any) -> str:
        module = load_print_templates()
        if module is not None and hasattr(module, name):
            template = getattr(module, name)
            if callable(template):
                return template(*args, **kwargs)
        return fallback(*args, **kwargs)

    return _render
