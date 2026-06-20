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



def _clean_value(value: Any) -> str:
    """Format values for emergency browser HTML without Python repr noise."""
    if value is None:
        return ""
    try:
        from decimal import Decimal as _Decimal
        if isinstance(value, _Decimal):
            return format(value.normalize(), 'f').rstrip('0').rstrip('.') if value != 0 else '0'
    except Exception:
        pass
    try:
        if isinstance(value, float):
            return (f"{value:.6f}").rstrip('0').rstrip('.')
    except Exception:
        pass
    text = str(value)
    # Remove Decimal('...') fragments when callers pass mixed payloads from old
    # serialization paths.  The emergency renderer should never expose Python
    # object syntax to users.
    if text.startswith("Decimal('") and text.endswith("')"):
        return text[9:-2]
    return text


def _money(value: Any) -> str:
    try:
        from decimal import Decimal as _Decimal
        n = _Decimal(str(value or 0))
        return f"{n:,.2f}"
    except Exception:
        return _clean_value(value)


def _get(data: Any, *keys: str, default: Any = "") -> Any:
    if not isinstance(data, dict):
        return default
    for key in keys:
        if key in data and data.get(key) not in (None, ""):
            return data.get(key)
    return default


def _fallback_lines_table(lines: Any) -> str:
    headers = ["المادة", "الكمية", "الوحدة", "السعر", "الخصم", "الضريبة", "الإجمالي"]
    rows = []
    if isinstance(lines, (list, tuple)):
        for line in lines:
            if not isinstance(line, dict):
                continue
            rows.append([
                _get(line, "item_name", "name", "material_name"),
                _get(line, "qty", "quantity"),
                _get(line, "unit", "unit_name"),
                _money(_get(line, "unit_price", "price")),
                _money(_get(line, "discount", "discount_amount")),
                _money(_get(line, "tax", "tax_amount")),
                _money(_get(line, "line_total", "total")),
            ])
    if not rows:
        rows.append(["لا توجد بنود", "", "", "", "", "", ""])
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(_clean_value(c))}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _fallback_meta_table(rows: Iterable[Iterable[Any]]) -> str:
    html_rows = []
    for row in rows:
        cells = []
        for label, value in row:
            cells.append(f"<td><b>{html.escape(_clean_value(label))}</b><br>{html.escape(_clean_value(value))}</td>")
        html_rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>" + "".join(html_rows) + "</table>"


def _fallback_totals_table(data: dict, is_return: bool = False) -> str:
    rows = [
        ("الإجمالي قبل الخصم", _money(_get(data, "total_before_discount", "subtotal"))),
        ("الخصم", _money(_get(data, "discount_amount", "discount"))),
        ("الضريبة", _money(_get(data, "tax_amount", "tax"))),
        ("الإجمالي", _money(_get(data, "total", "refund_amount" if is_return else "total"))),
        ("المقبوض" if not is_return else "المردود", _money(_get(data, "paid_amount", "paid", "refund_amount"))),
        ("المتبقي", _money(_get(data, "remaining"))),
    ]
    body = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in rows)
    return f"<table><tbody>{body}</tbody></table>"


def _fallback_invoice_template(data: Any, *, is_return: bool = False) -> str:
    if not isinstance(data, dict):
        return _fallback_report_template("فاتورة", [[_clean_value(data)]], ["البيانات"])
    doc_type = _get(data, "return_type", "type")
    if is_return:
        title = "مرتجع بيع" if str(doc_type) in {"sale", "sale_return"} else "مرتجع شراء"
    else:
        title = "فاتورة مبيعات" if str(doc_type) == "sale" else "فاتورة مشتريات" if str(doc_type) == "purchase" else "فاتورة"
    ref = _get(data, "reference", "return_number", "return_no", "number", "id")
    party = _get(data, "party_name", "customer_name", "supplier_name", "entity_name")
    party_label = "الطرف"
    body = """
    <style>
    .fallback-print .title{{font-size:24px;font-weight:700;text-align:center;margin:0 0 14px;}}
    .fallback-print .section{{margin-top:14px;}}
    .fallback-print .totals{{max-width:360px;margin-right:auto;margin-top:14px;}}
    </style>
    <div class='fallback-print'>
      <div class='title'>{title}</div>
      {meta}
      <div class='section'>{lines}</div>
      <div class='totals'>{totals}</div>
      <div class='section'><b>ملاحظات:</b> {notes}</div>
    </div>
    """.format(
        title=html.escape(title),
        meta=_fallback_meta_table([
            [("الرقم", ref), ("التاريخ", _get(data, "date", "created_at")), (party_label, party)],
            [("المستودع", _get(data, "warehouse_name", "warehouse")), ("طريقة الدفع", _get(data, "payment_method")), ("العملة", _get(data, "currency", "original_currency"))],
            [("الفاتورة الأصلية", _get(data, "original_invoice", "original_invoice_id")), ("الحالة", _get(data, "payment_status", "status")), ("المستخدم", _get(data, "user_name", "created_by"))],
        ]),
        lines=_fallback_lines_table(_get(data, "lines", default=[])),
        totals=_fallback_totals_table(data, is_return=is_return),
        notes=html.escape(_clean_value(_get(data, "notes", "description"))),
    )
    return _html_doc(title, body)

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
        payload = args[0] if args else kwargs
        if name == "invoice_html":
            return _fallback_invoice_template(payload, is_return=False)
        if name == "return_html":
            return _fallback_invoice_template(payload, is_return=True)
        title = kwargs.get("title") or kwargs.get("reference") or name.replace("_", " ").title()
        if isinstance(payload, dict):
            rows = [[html.escape(_clean_value(k)), html.escape(_clean_value(v))] for k, v in payload.items() if k != 'lines']
            table = "<table><tbody>" + "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</tbody></table>"
            return _html_doc(str(title), table)
        body = f"<div style='border:1px solid #dbe3ef;padding:12px'>{html.escape(_clean_value(payload))}</div>"
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
