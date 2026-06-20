# -*- coding: utf-8 -*-
"""Professional, settings-driven RTL HTML print templates.

All printable documents in the client should pass through these templates so PDF,
preview and direct-print output share the same header, typography, table style,
footer, paper sizing and company metadata.
"""
from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Optional
import base64
from io import BytesIO
import datetime
import os



def _tr(key: str, **kwargs) -> str:
    """Translate template text using the configured print language.

    The UI language and the print/report language may differ per settings.
    Template generation must therefore avoid relying on the translator's global
    current UI language.
    """
    key = str(key)
    try:
        from i18n import translator as _translator
        try:
            from core.services.settings_service import settings_service
            lang = _translator.normalize_language(settings_service.print_language())
        except Exception:
            lang = _translator.DEFAULT_LANGUAGE
        table = getattr(_translator, '_translations', {})
        text = table.get(lang, {}).get(key) or table.get(_translator.DEFAULT_LANGUAGE, {}).get(key) or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
    except Exception:
        return key


def _settings_service():
    try:
        from core.services.settings_service import settings_service
        return settings_service
    except Exception:
        return None


def _s(value: Any) -> str:
    return escape("" if value is None else str(value))


def _value(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _img_src(path: str) -> str:
    """Return a URI usable by QTextDocument."""
    if not path:
        return ""
    if path.startswith(("data:", "file:", "http://", "https://")):
        return path
    try:
        if os.path.exists(path):
            return "file:///" + os.path.abspath(path).replace("\\", "/")
    except Exception:
        pass
    return path


def _image_data_uri(path: str) -> str:
    """Return an inline image URI suitable for browser HTML printing.

    Storing/printing the logo as a data URI is required in client-server mode:
    a filesystem path selected on one workstation is not guaranteed to exist on
    another workstation.  Existing data/file/http URIs remain supported.
    """
    value = str(path or '').strip()
    if not value:
        return ""
    if value.startswith('data:'):
        return value
    if value.startswith(('http://', 'https://', 'file:')):
        return value
    try:
        import mimetypes
        if os.path.exists(value):
            mime = mimetypes.guess_type(value)[0] or 'image/png'
            with open(value, 'rb') as fh:
                encoded = base64.b64encode(fh.read()).decode('ascii')
            return f'data:{mime};base64,{encoded}'
    except Exception:
        return ""
    return ""


def _qr_data_uri(payload: str) -> str:
    try:
        import qrcode
        img = qrcode.make(payload or "")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def _print_meta_line() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _settings() -> Dict[str, Any]:
    try:
        svc = _settings_service()
        if svc is None:
            return {}
        cfg = svc.get_printing_settings()
        return dict(cfg or {})
    except Exception:
        return {}


def _bool_setting(settings: Dict[str, Any], key: str, default: bool = True) -> bool:
    val = settings.get(key, default)
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("1", "true", "yes", "on", "نعم")


def _normalize_paper(paper: str = "default", settings: Optional[Dict[str, Any]] = None, doc_type: str = "invoice") -> str:
    settings = settings or _settings()
    if paper in (None, "", "default"):
        if doc_type == "report":
            paper = settings.get("report_template") or settings.get("default_paper") or "a4"
        elif doc_type == "voucher":
            paper = settings.get("voucher_template") or settings.get("invoice_template") or "a4"
        elif doc_type == "return":
            paper = settings.get("return_template") or settings.get("invoice_template") or "a4"
        elif doc_type in ("restaurant_receipt", "restaurant_kitchen"):
            paper = settings.get("restaurant_receipt_template") or settings.get("restaurant_template") or settings.get("receipt_template") or settings.get("invoice_template") or "thermal"
        elif doc_type in ("inventory", "inventory_transfer", "inventory_balances", "inventory_movements", "inventory_ledger"):
            paper = settings.get("inventory_print_template") or settings.get("report_template") or settings.get("default_paper") or "a4"
        elif doc_type in ("manufacturing", "manufacturing_bom", "manufacturing_pick_ticket", "manufacturing_cost_report"):
            paper = settings.get("manufacturing_print_template") or settings.get("production_order_template") or settings.get("report_template") or settings.get("default_paper") or "a4"
        else:
            paper = settings.get("invoice_template") or settings.get("default_paper") or "a4"
    return str(paper or "a4").lower()


def _paper_spec(paper: str, settings: Dict[str, Any]) -> Dict[str, str]:
    paper = (paper or "a4").lower()
    thermal_size = str(settings.get("thermal_size", "80mm")).lower()
    if paper in ("thermal", "receipt"):
        paper = "thermal58" if "58" in thermal_size else "thermal80"
    if paper == "thermal58":
        return {"class": "thermal58", "page": "58mm auto", "width": "58mm", "margin": "2.5mm", "font": "8.5pt"}
    if paper == "thermal80":
        return {"class": "thermal80", "page": "80mm auto", "width": "78mm", "margin": "3mm", "font": "9pt"}
    # QTextDocument handles A4 HTML most consistently when the sheet remains fluid.
    return {"class": "a4", "page": "A4", "width": "100%", "margin": "10mm", "font": str(settings.get("print_font_size", "10.5pt") or "10.5pt")}


def _accent(settings: Dict[str, Any]) -> str:
    value = str(settings.get("accent_color", "#1d4ed8") or "#1d4ed8")
    return value if value.startswith("#") and len(value) in (4, 7) else "#1d4ed8"


def _font_family(settings: Dict[str, Any]) -> str:
    family = settings.get("font_family") or "Tajawal, Arial, DejaVu Sans, sans-serif"
    return str(family)





def _document_language() -> str:
    try:
        from i18n.translator import normalize_language
        svc = _settings_service()
        return normalize_language(svc.print_language() if svc is not None else "ar")
    except Exception:
        return "ar"


def _document_direction() -> str:
    try:
        from i18n.translator import language_direction
        return language_direction(_document_language())
    except Exception:
        return "rtl"


_TITLE_MAP = {
    "invoices": "invoices",
    "invoice": "invoices",
    "sales_invoices": "sales_invoices",
    "sale_invoices": "sales_invoices",
    "purchase_invoices": "purchase_invoices",
    "purchases_invoices": "purchase_invoices",
    "items": "items",
    "products": "items",
    "customers": "customers",
    "suppliers": "suppliers",
    "categories": "categories",
    "users": "users",
    "vouchers": "vouchers",
    "warehouses": "warehouses",
    "cashboxes": "cashboxes",
    "banks": "cashboxes",
    "cash_bank": "cashboxes",
    "manufacturing": "manufacturing",
    "reports": "reports",
    "settings": "settings",
    "audit_log": "audit_log",
    "returns": "returns",
    "sales_returns": "sales_returns",
    "purchase_returns": "purchase_returns",
    "restaurant_receipt": "restaurant_receipt",
    "restaurant_kitchen_ticket": "restaurant_kitchen_ticket",
}

def _human_title(title: Any, fallback: Optional[str] = None) -> str:
    fallback = fallback or _tr("print_report_default")
    raw = str(title or "").strip()
    if not raw:
        return fallback
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in _TITLE_MAP:
        return _tr(_TITLE_MAP[key])
    # Hide internal object names like table_items or view_invoices.
    for prefix in ("table_", "view_", "widget_", "page_", "tbl_"):
        if key.startswith(prefix) and key[len(prefix):] in _TITLE_MAP:
            return _tr(_TITLE_MAP[key[len(prefix):]])
    # If it is a technical ASCII identifier, do not print it above the date.
    if raw.replace("_", "").replace("-", "").isascii() and any(ch.isalpha() for ch in raw):
        return fallback
    return raw


def _company_data(settings: Dict[str, Any]) -> Dict[str, str]:
    svc = _settings_service()
    try:
        info = svc.company_info() if svc is not None else {}
    except Exception:
        info = {}
    logo_data_uri = _value(info.get("logo_data_uri") or settings.get("logo_data_uri"))
    logo_path = _value(info.get("logo_path") or info.get("logo") or settings.get("logo_path"))
    logo_src = logo_data_uri or _image_data_uri(logo_path)
    try:
        from pathlib import Path as _Path
        if not logo_src and (not logo_path or not _Path(logo_path).exists()):
            from brand_assets import logo_png
            logo_path = logo_png(512)
            logo_src = _image_data_uri(logo_path) or _img_src(logo_path)
    except Exception:
        logo_src = logo_src or (_img_src(logo_path) if logo_path else "")
    return {
        "name": _value(info.get("name") or settings.get("company_name"), _tr("app_title")),
        "address": _value(info.get("address") or settings.get("company_address")),
        "phone": _value(info.get("phone") or settings.get("company_phone")),
        "email": _value(info.get("email") or settings.get("company_email")),
        "tax_number": _value(info.get("tax_number") or settings.get("tax_number")),
        "logo_path": logo_path,
        "logo_src": logo_src,
        "logo_data_uri": logo_data_uri,
        "commercial_register": _value(info.get("commercial_register") or settings.get("commercial_register")),
        "website": _value(info.get("website") or settings.get("company_website")),
    }


def _company_header(settings: Dict[str, Any], title: str = "") -> str:
    title = _human_title(title, _tr("print_document"))
    data = _company_data(settings)
    logo_html = ""
    logo_src = data.get("logo_src") or _image_data_uri(data.get("logo_path")) or _img_src(data.get("logo_path", ""))
    if logo_src and _bool_setting(settings, "show_logo", True):
        logo_html = f"<td class='brand-logo'><img src='{_s(logo_src)}' alt='logo'></td>"
    else:
        logo_html = "<td class='brand-logo placeholder'> </td>"

    # Phase 243: company identity lines are all settings-governed and come
    # from the SettingsService/SettingsGateway contract, so client-server users
    # and profiles get the same browser HTML output in Arabic, English or German.
    name_line = f"<div class='company-name'>{_s(data['name'])}</div>" if _bool_setting(settings, "show_company_name", True) else ""
    address_line = f"<div class='muted'>{_s(data['address'])}</div>" if data.get("address") and _bool_setting(settings, "show_address", True) else ""
    tax_line = ""
    if data["tax_number"] and _bool_setting(settings, "show_tax_number", True):
        tax_line = f"<div class='muted'>{_s(_tr('print_tax_number'))}: {_s(data['tax_number'])}</div>"
    cr_line = f"<div class='muted'>{_s(_tr('print_commercial_register'))}: {_s(data['commercial_register'])}</div>" if data.get("commercial_register") and _bool_setting(settings, "show_commercial_register", True) else ""
    website_line = f"<div class='muted'>{_s(data['website'])}</div>" if data.get("website") and _bool_setting(settings, "show_website", True) else ""

    contacts = []
    if data["phone"] and _bool_setting(settings, "show_phone", True):
        contacts.append(_tr("print_phone") + ": " + _s(data["phone"]))
    if data["email"] and _bool_setting(settings, "show_email", True):
        contacts.append(_tr("print_email") + ": " + _s(data["email"]))
    contact_line = " | ".join(contacts)
    contact_line_html = f"<div class='muted'>{contact_line}</div>" if contact_line else ""

    return f"""
    <table class='brand-table'>
        <tr>
            {logo_html}
            <td class='brand-main'>
                {name_line}
                {address_line}
                {contact_line_html}
                {tax_line}
                {cr_line}
                {website_line}
            </td>
            <td class='brand-meta'>
                <div class='document-badge'>{_s(title)}</div>
                <div class='muted'>{_s(_tr("print_date_label"))}</div>
                <div class='strong'>{_print_meta_line()}</div>
            </td>
        </tr>
    </table>
    """


def _meta_table(rows: List[List[tuple]]) -> str:
    out = []
    for row in rows:
        cells = []
        for label, value in row:
            cells.append(f"<td><span class='meta-label'>{_s(label)}</span><span class='meta-value'>{_s(value)}</span></td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return "<table class='meta-table'>" + "".join(out) + "</table>"


def _totals_table(rows: List[tuple]) -> str:
    body = []
    for label, value, klass in rows:
        cls = f" class='{_s(klass)}'" if klass else ""
        body.append(f"<tr{cls}><td>{_s(label)}</td><td>{_s(value)}</td></tr>")
    return "<table class='totals-table'>" + "".join(body) + "</table>"


def _line_value(line: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = line.get(key) if isinstance(line, dict) else None
        if value not in (None, ""):
            return value
    return default


def _table(headers: List[str], rows: List[List[Any]], empty_text: str = _tr("print_no_data"), reverse_columns: Optional[bool] = None) -> str:
    """Render a professional RTL-safe table.

    Qt QTextDocument sometimes mirrors RTL table visual order differently between
    preview and PDF. We therefore reverse columns in the generated HTML by
    default, so the final PDF appears in the intended Arabic order. This can be
    disabled from printing settings with reverse_print_table_columns = false.
    """
    settings = _settings()
    if reverse_columns is None:
        reverse_columns = _bool_setting(settings, "reverse_print_table_columns", False)

    safe_headers = list(headers or [])
    safe_rows = [list(row or []) for row in (rows or [])]
    if reverse_columns and len(safe_headers) > 1:
        safe_headers = list(reversed(safe_headers))
        safe_rows = [list(reversed(row)) for row in safe_rows]

    head = "".join(f"<th>{_s(h)}</th>" for h in safe_headers)
    body = []
    for row in safe_rows:
        # Keep row length aligned with header count for stable PDF rendering.
        if len(row) < len(safe_headers):
            row = row + [""] * (len(safe_headers) - len(row))
        elif len(row) > len(safe_headers) and safe_headers:
            row = row[:len(safe_headers)]
        body.append("<tr>" + "".join(f"<td>{_s(c)}</td>" for c in row) + "</tr>")
    if not body:
        body.append(f"<tr><td colspan='{max(1, len(safe_headers))}' class='empty-cell'>{_s(empty_text)}</td></tr>")
    table_dir = _document_direction()
    return f"<table class='data-table' dir='{table_dir}'><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _summary_cards(summary: Optional[Dict[str, Any]]) -> str:
    if not summary:
        return ""
    cells = []
    for key, value in summary.items():
        cells.append(f"<td class='summary-card'><div class='summary-label'>{_s(key)}</div><div class='summary-value'>{_s(value)}</div></td>")
    return "<table class='summary-table'><tr>" + "".join(cells) + "</tr></table>"


def _footer(settings: Dict[str, Any], default: str = "") -> str:
    text = settings.get("footer_text") or default or _tr("print_generated_by")
    return f"<div class='print-footer'>{_s(text)}</div>"


def base_document(title: str, body_html: str, paper: str = "a4", settings: Optional[Dict[str, Any]] = None) -> str:
    settings = settings or _settings()
    spec = _paper_spec(paper, settings)
    lang = _document_language()
    doc_dir = _document_direction()
    text_align = 'right' if doc_dir == 'rtl' else 'left'
    opposite_align = 'left' if doc_dir == 'rtl' else 'right'
    accent = _accent(settings)
    font_family = _font_family(settings)
    compact = " compact" if _bool_setting(settings, "compact_tables", False) else ""
    zebra = " zebra" if _bool_setting(settings, "zebra_rows", True) else ""

    # Use table-based layout because Qt QTextDocument renders it more reliably than flex/grid in PDF.
    return f"""<!DOCTYPE html>
<html dir='{doc_dir}' lang='{lang}'>
<head>
<meta charset='utf-8'>
<title>{_s(title)}</title>
<style>
@page {{ size: {spec['page']}; margin: {spec['margin']}; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #ffffff; color: #111827; direction: {doc_dir}; }}
body {{ font-family: {font_family}; font-size: {spec['font']}; line-height: 1.45; }}
.sheet {{ width: {spec['width']}; margin: 0 auto; }}
.brand-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; border-bottom: 3px solid {accent}; }}
.brand-table td {{ vertical-align: middle; padding: 8px 6px; border: none; }}
.brand-logo {{ width: 90px; text-align: center; }}
.brand-logo img {{ max-width: 78px; max-height: 70px; }}
.brand-logo.placeholder {{ border: 1px dashed #d1d5db; border-radius: 8px; }}
.brand-main {{ text-align: {text_align}; }}
.company-name {{ font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 2px; }}
.brand-meta {{ width: 155px; text-align: center; border-right: 1px solid #e5e7eb !important; }}
.document-badge {{ display: inline-block; background: {accent}; color: #ffffff; padding: 7px 12px; border-radius: 999px; font-weight: 800; margin-bottom: 5px; }}
.muted {{ color: #64748b; font-size: 90%; }}
.strong {{ font-weight: 800; color: #111827; }}
.document-title {{ text-align: center; font-size: 18px; font-weight: 900; margin: 8px 0 10px; color: #0f172a; }}
.meta-table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px; }}
.meta-table td {{ border: 1px solid #dbe3ef; background: #f8fafc; padding: 7px 9px; width: 33.33%; }}
.meta-label {{ display: block; color: #64748b; font-size: 88%; margin-bottom: 2px; }}
.meta-value {{ display: block; font-weight: 800; color: #0f172a; }}
.data-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 8px; direction: {doc_dir}; }}
.data-table th {{ background: {accent}; color: #ffffff; border: 1px solid {accent}; padding: 8px 5px; font-weight: 800; text-align: center; white-space: normal; }}
.data-table td {{ border: 1px solid #dbe3ef; padding: 7px 5px; text-align: center; vertical-align: middle; word-wrap: break-word; overflow-wrap: anywhere; }}
.data-table tbody tr:nth-child(even) td {{ background: #f8fafc; }}
.data-table thead {{ display: table-header-group; }}
.data-table tr {{ page-break-inside: avoid; }}
.data-table .text-cell {{ text-align: {text_align}; }}
.empty-cell {{ color: #64748b; padding: 20px !important; }}
.summary-table {{ width: 100%; border-collapse: separate; border-spacing: 6px; margin: 9px 0; }}
.summary-card {{ border: 1px solid #dbe3ef; background: #f8fafc; border-radius: 10px; padding: 8px; text-align: center; }}
.summary-label {{ color: #64748b; font-size: 88%; }}
.summary-value {{ color: #0f172a; font-size: 115%; font-weight: 900; margin-top: 2px; }}
.totals-table {{ width: 42%; min-width: 260px; margin-{opposite_align}: auto; margin-top: 10px; border-collapse: collapse; }}
.totals-table td {{ border: 1px solid #dbe3ef; padding: 7px 9px; }}
.totals-table td:first-child {{ background: #f8fafc; color: #334155; font-weight: 700; }}
.totals-table td:last-child {{ text-align: {text_align}; font-weight: 800; }}
.totals-table tr.final td {{ background: #eaf2ff; color: #0f172a; font-size: 110%; }}
.totals-table tr.due td:last-child {{ color: #dc2626; }}
.notes-box {{ margin-top: 10px; border: 1px dashed #cbd5e1; background: #fcfdff; padding: 8px; min-height: 34px; }}
.qr-table {{ width: 100%; margin-top: 10px; border-collapse: collapse; }}
.qr-table td {{ text-align: center; border: none; color: #64748b; }}
.qr-table img {{ width: 88px; height: 88px; }}
.signatures {{ width: 100%; border-collapse: collapse; margin-top: 28px; }}
.signatures td {{ width: 50%; text-align: center; padding-top: 22px; border-top: 1px solid #475569; color: #334155; }}
.signatures td:first-child {{ padding-right: 30px; }}
.signatures td:last-child {{ padding-left: 30px; }}
.print-footer {{ margin-top: 18px; padding-top: 8px; border-top: 1px solid #e5e7eb; text-align: center; color: #64748b; font-size: 90%; }}
.compact .data-table th, .compact .data-table td, .compact .meta-table td, .compact .totals-table td {{ padding: 4px 3px; }}
.thermal80 .sheet, .thermal58 .sheet {{ width: {spec['width']}; }}
.thermal80 .brand-table, .thermal58 .brand-table {{ border-bottom-width: 1px; margin-bottom: 5px; }}
.thermal80 .brand-logo, .thermal58 .brand-logo {{ display: none; }}
.thermal80 .brand-meta, .thermal58 .brand-meta {{ display: none; }}
.thermal80 .company-name, .thermal58 .company-name {{ font-size: 12px; text-align: center; }}
.thermal80 .muted, .thermal58 .muted {{ font-size: 8px; text-align: center; }}
.thermal80 .document-title, .thermal58 .document-title {{ font-size: 12px; margin: 4px 0; }}
.thermal80 .data-table th, .thermal80 .data-table td, .thermal58 .data-table th, .thermal58 .data-table td {{ padding: 2px; font-size: 8px; }}
.thermal80 .meta-table td, .thermal58 .meta-table td {{ display: table-cell; padding: 2px; font-size: 8px; }}
.thermal80 .totals-table, .thermal58 .totals-table {{ width: 100%; min-width: 0; }}
.thermal80 .signatures, .thermal58 .signatures {{ display: none; }}
.thermal80 .hide-thermal, .thermal58 .hide-thermal {{ display: none; }}
</style>
</head>
<body class='{_s(spec['class'])}{compact}{zebra}'>
<div class='sheet'>
{body_html}
</div>
</body>
</html>"""


def invoice_html(invoice: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "invoice")
    inv_type = invoice.get("type") or invoice.get("inv_type") or "sale"
    title = {"sale": _tr("sales_invoice"), "purchase": _tr("purchase_invoice")}.get(inv_type, _tr("invoice"))
    ref = invoice.get("reference") or invoice.get("ref") or invoice.get("number") or invoice.get("id") or ""
    date = invoice.get("date") or invoice.get("created_at") or ""
    party_label = _tr("print_party_customer") if inv_type == "sale" else _tr("print_party_supplier")
    party = invoice.get("party_name") or invoice.get("entity_name") or invoice.get("customer_name") or invoice.get("supplier_name") or _tr("print_cash_party")
    warehouse = invoice.get("warehouse_name") or invoice.get("warehouse") or ""
    payment_method = invoice.get("payment_method") or invoice.get("payment") or ""
    user_name = invoice.get("user_name") or invoice.get("seller_name") or invoice.get("created_by") or ""

    raw_lines: Iterable[Any] = invoice.get("lines") or invoice.get("items") or []
    rows: List[List[Any]] = []
    for i, raw in enumerate(raw_lines, 1):
        line = raw if isinstance(raw, dict) else {}
        rows.append([
            i,
            _line_value(line, "barcode", "item_barcode", "code"),
            _line_value(line, "item_name", "name", "description"),
            _line_value(line, "unit", "unit_display", "unit_name"),
            _line_value(line, "quantity", "qty"),
            _line_value(line, "unit_price", "price"),
            _line_value(line, "discount_percent", "discount_pct", "discount", default="0"),
            _line_value(line, "tax_percent", "tax_pct", "tax", default="0"),
            _line_value(line, "line_total", "total"),
        ])

    qr_html = ""
    if _bool_setting(settings, "show_qr", True):
        qr_payload = f"INV|{ref}|{date}|{invoice.get('total', '')}|{party}"
        qr_uri = _qr_data_uri(qr_payload)
        if qr_uri:
            qr_html = f"<table class='qr-table'><tr><td><img src='{qr_uri}'><div>{_s(_tr("print_document_qr"))}</div></td></tr></table>"

    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr("print_document_number"), ref), (_tr("print_document_date"), date), (party_label, party)],
        [(_tr("print_warehouse"), warehouse), (_tr("print_payment_method"), payment_method), (_tr("print_user"), user_name)],
    ])}
    {_table(["#", _tr("print_barcode"), _tr("print_item"), _tr("print_unit"), _tr("print_quantity"), _tr("print_price"), _tr("print_discount_percent"), _tr("print_tax_percent"), _tr("print_total")], rows, _tr("print_no_lines"))}
    {_totals_table([
        (_tr("print_subtotal"), invoice.get("total_before_discount", invoice.get("subtotal", "")), ""),
        (_tr("print_discount"), invoice.get("discount", invoice.get("discount_amount", 0)), ""),
        (_tr("print_tax"), invoice.get("tax_amount", invoice.get("tax", 0)), ""),
        (_tr("print_grand_total"), invoice.get("total", ""), "final"),
        (_tr("print_paid"), invoice.get("paid") or invoice.get("paid_amount", 0), ""),
        (_tr("print_remaining"), invoice.get("remaining", ""), "due"),
    ])}
    <div class='notes-box'><b>{_s(_tr("print_notes"))}:</b> {_s(invoice.get('notes', ''))}</div>
    {qr_html}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr("print_receiver_signature"))}</td><td>{_s(_tr("print_accountant_signature"))}</td></tr></table>
    {_footer(settings, _tr("print_thanks"))}
    """
    return base_document(f"{title} {ref}", body, paper, settings)


def voucher_html(voucher: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "voucher")
    vtype = voucher.get("type")
    title = {"receipt": _tr("receipt_voucher"), "payment": _tr("payment_voucher"), "expense": _tr("expense_voucher")}.get(vtype, _tr("voucher"))
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr("print_number"), voucher.get("id") or voucher.get("reference")), (_tr("print_document_date"), voucher.get("date")), (_tr("amount"), voucher.get("amount"))],
        [(_tr("print_party"), voucher.get("party_name", "")), (_tr("print_account"), voucher.get("account_name", "")), (_tr("print_user"), voucher.get("user_name", ""))],
    ])}
    <div class='notes-box'><b>{_s(_tr("print_description"))}:</b> {_s(voucher.get('description', ''))}</div>
    <table class='signatures'><tr><td>{_s(_tr("print_receiver"))}</td><td>{_s(_tr("print_accountant_signature"))}</td></tr></table>
    {_footer(settings, title)}
    """
    return base_document(title, body, paper, settings)


def return_html(data: Dict[str, Any], paper: str = "default") -> str:
    payload = dict(data or {})
    rtype = payload.get("type") or payload.get("return_type") or "sale_return"
    payload["type"] = "sale" if rtype in ("sale_return", "sale") else "purchase"
    payload["reference"] = payload.get("reference") or payload.get("return_number") or payload.get("id") or ""
    title = _tr("sales_return") if payload["type"] == "sale" else _tr("purchase_return")
    html = invoice_html(payload, _normalize_paper(paper, _settings(), "return"))
    return html.replace(_tr("sales_invoice"), title).replace(_tr("purchase_invoice"), title)


def report_html(title: str, rows: List[List[Any]], headers: List[str], subtitle: str = "", summary: Optional[Dict[str, Any]] = None, paper: str = "default") -> str:
    settings = _settings()
    title = _human_title(title, _tr("print_report_default"))
    paper = _normalize_paper(paper, settings, "report")
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    <div class='muted' style='text-align:center;margin-bottom:8px;'>{_s(subtitle)}</div>
    {_summary_cards(summary)}
    {_table(headers, rows, _tr("print_no_data"))}
    {_footer(settings, _tr("print_report_generated_by"))}
    """
    return base_document(title, body, paper, settings)



def _restaurant_line_total(line: Dict[str, Any]) -> Any:
    try:
        from decimal import Decimal
        return str(Decimal(str(line.get("quantity") or "0")) * Decimal(str(line.get("unit_price") or "0")))
    except Exception:
        return line.get("total") or line.get("line_total") or "0"


def restaurant_receipt_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Settings-driven customer receipt for Restaurant POS sessions."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "restaurant_receipt")
    session = dict((data or {}).get("session") or data or {})
    balance = dict((data or {}).get("balance") or {})
    lines = list(session.get("lines") or (data or {}).get("lines") or [])
    payments = list(session.get("payments") or (data or {}).get("payments") or [])
    title = _tr("restaurant_receipt")
    ref = session.get("invoice_reference") or session.get("invoice_id") or session.get("id") or ""
    table = session.get("table_name") or session.get("table_id") or ""
    opened = session.get("opened_at") or session.get("created_at") or ""
    closed = session.get("closed_at") or ""
    guests = session.get("guests") or ""
    waiter = session.get("waiter_name") or session.get("waiter_id") or session.get("user_name") or ""

    rows: List[List[Any]] = []
    for i, raw in enumerate(lines, 1):
        line = raw if isinstance(raw, dict) else {}
        status = line.get("kitchen_status") or ""
        rows.append([
            i,
            _line_value(line, "item_name", "name", "description"),
            _line_value(line, "unit", "unit_name"),
            _line_value(line, "quantity", "qty"),
            _line_value(line, "base_qty", "quantity_in_base"),
            _line_value(line, "unit_price", "price"),
            _restaurant_line_total(line),
            _tr(f"restaurant.line_status.{status}") if status else "",
        ])

    payment_rows: List[List[Any]] = []
    for i, raw in enumerate(payments, 1):
        pay = raw if isinstance(raw, dict) else {}
        payment_rows.append([
            i,
            pay.get("payment_method") or pay.get("method") or "",
            pay.get("amount") or "",
            pay.get("created_at") or pay.get("date") or "",
            pay.get("notes") or "",
        ])

    subtotal = balance.get("subtotal", session.get("subtotal", ""))
    discount = balance.get("discount_amount", session.get("discount_amount", "0"))
    service_charge = balance.get("service_charge_amount", session.get("service_charge_amount", "0"))
    tax = balance.get("tax_amount", session.get("tax_amount", "0"))
    total = balance.get("total", session.get("invoice_total", session.get("total", "")))
    paid = balance.get("paid", session.get("paid_amount", "0"))
    remaining = balance.get("remaining", session.get("remaining", "0"))

    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr("print_document_number"), ref), (_tr("restaurant_table"), table), (_tr("restaurant_guests"), guests)],
        [(_tr("restaurant_opened_at"), opened), (_tr("restaurant_closed_at"), closed), (_tr("restaurant_waiter"), waiter)],
    ])}
    {_table(["#", _tr("print_item"), _tr("print_unit"), _tr("print_quantity"), _tr("pos_column_base_qty"), _tr("print_price"), _tr("print_total"), _tr("restaurant_column_status")], rows, _tr("print_no_lines"))}
    {_totals_table([
        (_tr("print_subtotal"), subtotal, ""),
        (_tr("print_discount"), discount, ""),
        (_tr("restaurant.service_charge"), service_charge, ""),
        (_tr("print_tax"), tax, ""),
        (_tr("print_total"), total, "final"),
        (_tr("restaurant.paid"), paid, ""),
        (_tr("restaurant.remaining"), remaining, "due"),
    ])}
    <div class='notes-box'><strong>{_s(_tr("print_notes"))}</strong>: {_s(session.get("notes") or "")}</div>
    {_table(["#", _tr("print_payment_method"), _tr("restaurant.payment_amount"), _tr("print_document_date"), _tr("print_notes")], payment_rows, _tr("restaurant.no_payments")) if payment_rows else ""}
    {_footer(settings)}
    """
    return base_document(title, body, paper, settings)


def restaurant_kitchen_ticket_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Settings-driven kitchen order ticket (KOT)."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "restaurant_kitchen")
    ticket = dict(data or {})
    lines = list(ticket.get("lines") or [])
    title = _tr("restaurant_kitchen_ticket")
    rows: List[List[Any]] = []
    for i, raw in enumerate(lines, 1):
        line = raw if isinstance(raw, dict) else {}
        rows.append([
            i,
            _line_value(line, "item_name", "name"),
            _line_value(line, "quantity", "qty"),
            _line_value(line, "unit", "unit_name", default=""),
            _line_value(line, "station_name", "station_code", default=""),
            _line_value(line, "notes", "kitchen_label", default=""),
        ])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr("print_document_number"), ticket.get("id") or ""), (_tr("restaurant_table"), ticket.get("table_name") or ticket.get("table_id") or ""), (_tr("restaurant_station"), ticket.get("station_name") or ticket.get("station_code") or "")],
        [(_tr("restaurant_sent_at"), ticket.get("sent_at") or ""), (_tr("restaurant_ticket_status"), ticket.get("status") or ""), (_tr("print_notes"), ticket.get("notes") or "")],
    ])}
    {_table(["#", _tr("print_item"), _tr("print_quantity"), _tr("print_unit"), _tr("restaurant_station"), _tr("print_notes")], rows, _tr("print_no_lines"))}
    {_footer(settings, _tr("restaurant_kitchen_ticket_footer"))}
    """
    return base_document(title, body, paper, settings)


def _manufacturing_status(value: Any) -> str:
    status_map = {
        'planned': _tr('status_planned'),
        'in_progress': _tr('status_in_progress'),
        'completed': _tr('status_completed'),
        'cancelled': _tr('status_cancelled'),
    }
    return status_map.get(str(value or ''), str(value or ''))


def manufacturing_bom_html(data: Dict[str, Any], paper: str = "default") -> str:
    """BOM / manufacturing recipe print template."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing_bom")
    payload = dict(data or {})
    bom = payload.get('bom') or payload
    lines = list(payload.get('lines') or bom.get('lines') or bom.get('components') or [])
    summary = payload.get('summary') or {}
    title = _tr('manufacturing_bom_document')
    rows: List[List[Any]] = []
    for i, row in enumerate(lines, 1):
        qty = _line_value(row, 'quantity', 'qty', 'component_qty')
        base_qty = _line_value(row, 'base_qty', 'required_base_qty')
        rows.append([
            i,
            _line_value(row, 'barcode', 'matched_barcode'),
            _line_value(row, 'item_name', 'name', 'item', 'component_name', default=row.get('item_id', '')),
            _line_value(row, 'unit_name', 'unit', default=''),
            qty,
            base_qty,
            _line_value(row, 'waste_percent', default=''),
            _line_value(row, 'unit_cost', 'cost', default=''),
            _line_value(row, 'total_cost', default=''),
            _line_value(row, 'notes', default=''),
        ])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr('print_product'), bom.get('product_name') or bom.get('item_name') or bom.get('product_id') or ''), (_tr('print_quantity'), bom.get('output_qty') or bom.get('quantity') or 1), (_tr('status'), bom.get('status') or '')],
        [(_tr('print_document_number'), bom.get('id') or bom.get('bom_id') or ''), (_tr('print_unit'), bom.get('unit_name') or bom.get('unit') or ''), (_tr('print_notes'), bom.get('notes') or '')],
    ])}
    {_table(['#', _tr('print_barcode'), _tr('print_item'), _tr('print_unit'), _tr('print_quantity'), _tr('manufacturing_column_base_qty'), _tr('manufacturing_column_waste_percent'), _tr('unit_cost'), _tr('print_total'), _tr('print_notes')], rows, _tr('print_no_lines'))}
    {_summary_cards({
        _tr('manufacturing_material_cost'): summary.get('material_cost', ''),
        _tr('manufacturing_waste_cost'): summary.get('waste_cost', ''),
        _tr('print_total'): summary.get('total_cost', ''),
        _tr('manufacturing_unit_cost_output'): summary.get('unit_cost_output', ''),
        _tr('manufacturing_component_count'): summary.get('line_count', len(lines)),
    })}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('production_manager'))}</td><td>{_s(_tr('print_accountant_signature'))}</td></tr></table>
    {_footer(settings, _tr('manufacturing_bom_generated_by'))}
    """
    return base_document(title, body, paper, settings)


def production_order_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Professional HTML for production order details."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing")
    payload = dict(data or {})
    order = payload.get("order") or payload
    consumptions = payload.get("consumptions") or []
    outputs = payload.get("outputs") or []
    reservations = payload.get("reservations") or []
    title = _tr("production_order")
    meta = _meta_table([
        [(_tr("order_number"), order.get("order_number") or order.get("id") or ""), (_tr("product"), order.get("product_name") or order.get("item_name") or ""), (_tr("status"), _manufacturing_status(order.get("status")))],
        [(_tr("planned_quantity"), order.get("planned_qty", "")), (_tr("produced_quantity"), order.get("produced_qty", "")), (_tr("start_date"), order.get("start_date", ""))],
        [(_tr("raw_warehouse"), order.get("raw_warehouse_name") or ""), (_tr("output_warehouse"), order.get("output_warehouse_name") or ""), (_tr("print_notes"), order.get("notes", ""))],
    ])
    cons_rows = []
    for i, c in enumerate(consumptions, 1):
        cons_rows.append([i, _line_value(c, 'item_name', 'name', 'item', default=c.get('item_id', '')), _line_value(c, 'unit_name', 'unit'), _line_value(c, 'consumed_qty', 'quantity', 'qty'), _line_value(c, 'consumed_base_qty', 'base_qty'), _line_value(c, 'unit_cost', 'cost'), _line_value(c, 'total_cost'), _line_value(c, 'movement_date', 'date')])
    out_rows = []
    for i, o in enumerate(outputs, 1):
        out_rows.append([i, _line_value(o, 'product_name', 'item_name', 'name', 'item', default=o.get('product_id', '')), _line_value(o, 'unit_name', 'unit'), _line_value(o, 'produced_qty', 'quantity', 'qty'), _line_value(o, 'produced_base_qty', 'base_qty'), _line_value(o, 'unit_cost', 'cost'), _line_value(o, 'total_cost'), _line_value(o, 'output_date', 'date')])
    res_rows = []
    for i, r in enumerate(reservations, 1):
        reserved = _line_value(r, 'reserved_qty', 'reserved', 'required_qty')
        consumed = _line_value(r, 'consumed_qty', 'consumed')
        remaining = _line_value(r, 'remaining_qty', 'remaining')
        res_rows.append([i, _line_value(r, 'item_name', 'name', 'item', default=r.get('item_id', '')), _line_value(r, 'unit_name', 'unit'), reserved, consumed, remaining, _line_value(r, 'base_qty', 'reserved_base_qty'), _line_value(r, 'conversion_factor')])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {meta}
    <h3>{_s(_tr('consumed_materials'))}</h3>
    {_table(['#', _tr('print_item'), _tr('print_unit'), _tr('print_quantity'), _tr('manufacturing_column_base_qty'), _tr('unit_cost'), _tr('print_total'), _tr('print_document_date')], cons_rows, _tr('print_no_consumed_materials'))}
    <h3>{_s(_tr('finished_product'))}</h3>
    {_table(['#', _tr('print_product'), _tr('print_unit'), _tr('print_quantity'), _tr('manufacturing_column_base_qty'), _tr('unit_cost'), _tr('print_total'), _tr('print_document_date')], out_rows, _tr('print_no_production_outputs'))}
    <h3>{_s(_tr('reservations_remaining'))}</h3>
    {_table(['#', _tr('print_item'), _tr('print_unit'), _tr('reserved'), _tr('consumed'), _tr('print_remaining'), _tr('manufacturing_column_base_qty'), _tr('manufacturing_column_conversion_factor')], res_rows, _tr('print_no_reservations'))}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('production_manager'))}</td><td>{_s(_tr('print_accountant_signature'))}</td></tr></table>
    {_footer(settings, _tr('production_order_generated_by'))}
    """
    return base_document(title, body, paper, settings)


def manufacturing_pick_ticket_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Raw-material pick ticket for production."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing_pick_ticket")
    payload = dict(data or {})
    order = payload.get('order') or {}
    lines = list(payload.get('lines') or payload.get('reservations') or [])
    title = _tr('manufacturing_pick_ticket')
    rows: List[List[Any]] = []
    for i, row in enumerate(lines, 1):
        rows.append([i, _line_value(row, 'item_name', 'name', 'item', default=row.get('item_id', '')), _line_value(row, 'barcode', 'matched_barcode'), _line_value(row, 'unit_name', 'unit'), _line_value(row, 'pick_qty', 'remaining_qty'), _line_value(row, 'reserved_qty'), _line_value(row, 'consumed_qty'), _line_value(row, 'base_qty', 'reserved_base_qty'), _line_value(row, 'raw_warehouse_name', 'warehouse_name')])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr('order_number'), order.get('order_number') or order.get('id') or ''), (_tr('product'), order.get('product_name') or order.get('item_name') or ''), (_tr('status'), _manufacturing_status(order.get('status')))],
        [(_tr('raw_warehouse'), order.get('raw_warehouse_name') or ''), (_tr('planned_quantity'), order.get('planned_qty') or ''), (_tr('print_notes'), order.get('notes') or '')],
    ])}
    {_table(['#', _tr('print_item'), _tr('print_barcode'), _tr('print_unit'), _tr('manufacturing_pick_qty'), _tr('reserved'), _tr('consumed'), _tr('manufacturing_column_base_qty'), _tr('print_warehouse')], rows, _tr('print_no_reservations'))}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('warehouse_keeper'))}</td><td>{_s(_tr('production_manager'))}</td></tr></table>
    {_footer(settings, _tr('manufacturing_pick_ticket_footer'))}
    """
    return base_document(title, body, paper, settings)


def manufacturing_cost_report_html(data: Dict[str, Any], paper: str = "default") -> str:
    """Production cost report template."""
    settings = _settings()
    paper = _normalize_paper(paper, settings, "manufacturing_cost_report")
    payload = dict(data or {})
    order = payload.get('order') or {}
    summary = payload.get('summary') or {}
    title = _tr('manufacturing_cost_report')
    rows = [
        [_tr('manufacturing_consumption_cost'), summary.get('consumption_cost', '')],
        [_tr('manufacturing_output_cost'), summary.get('output_cost', '')],
        [_tr('manufacturing_cost_variance'), summary.get('variance_cost', '')],
        [_tr('produced_quantity'), summary.get('produced_qty', '')],
        [_tr('unit_cost'), summary.get('unit_cost', '')],
    ]
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr('order_number'), order.get('order_number') or order.get('id') or ''), (_tr('product'), order.get('product_name') or order.get('item_name') or ''), (_tr('status'), _manufacturing_status(order.get('status')))],
        [(_tr('planned_quantity'), order.get('planned_qty') or ''), (_tr('produced_quantity'), order.get('produced_qty') or ''), (_tr('print_notes'), order.get('notes') or '')],
    ])}
    {_table([_tr('print_description'), _tr('print_total')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('manufacturing_cost_report_footer'))}
    """
    return base_document(title, body, paper, settings)


# ========== Inventory / warehouse templates ==========
def _inventory_movement_type(value: Any) -> str:
    key = str(value or '').strip()
    if not key:
        return ''
    label = _tr(f'inventory_movement_type_{key}')
    return label if label != f'inventory_movement_type_{key}' else key


def inventory_transfer_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_transfer")
    payload = dict(data or {})
    transfer = payload.get('transfer') or payload
    lines = list(payload.get('lines') or ([] if transfer is payload else [transfer]))
    title = _tr('inventory_transfer_document')
    rows: List[List[Any]] = []
    for i, row in enumerate(lines, 1):
        rows.append([
            i,
            _line_value(row, 'item_name', 'name', 'item', default=row.get('item_id', '')),
            _line_value(row, 'barcode', 'matched_barcode'),
            _line_value(row, 'unit_name', 'unit'),
            _line_value(row, 'quantity', 'qty'),
            _line_value(row, 'base_qty', 'quantity_in_base', default=_line_value(row, 'quantity', 'qty')),
            _line_value(row, 'unit_cost', 'cost'),
            _line_value(row, 'notes'),
        ])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([
        [(_tr('transfer_no'), transfer.get('transfer_no') or transfer.get('id') or ''), (_tr('status'), transfer.get('status') or ''), (_tr('print_date'), transfer.get('created_at') or '')],
        [(_tr('from_warehouse_clean'), transfer.get('from_warehouse_name') or transfer.get('from_warehouse') or ''), (_tr('to_warehouse_clean'), transfer.get('to_warehouse_name') or transfer.get('to_warehouse') or ''), (_tr('print_notes'), transfer.get('notes') or '')],
    ])}
    {_table(['#', _tr('print_item'), _tr('print_barcode'), _tr('print_unit'), _tr('quantity'), _tr('inventory_column_base_qty'), _tr('unit_cost'), _tr('print_notes')], rows, _tr('print_no_data'))}
    <table class='signatures hide-thermal'><tr><td>{_s(_tr('warehouse_keeper'))}</td><td>{_s(_tr('receiver_signature'))}</td></tr></table>
    {_footer(settings, _tr('inventory_transfer_footer'))}
    """
    return base_document(title, body, paper, settings)


def inventory_balances_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_balances")
    payload = dict(data or {})
    rows_data = list(payload.get('rows') or payload.get('balances') or [])
    title = _tr('inventory_balances_report')
    rows: List[List[Any]] = []
    for i, row in enumerate(rows_data, 1):
        rows.append([i, _line_value(row, 'item_name', 'name', default=row.get('item_id', '')), _line_value(row, 'barcode'), _line_value(row, 'warehouse_name', 'warehouse'), _line_value(row, 'quantity', 'available_qty', 'balance'), _line_value(row, 'unit_name', 'unit'), _line_value(row, 'inventory_value', 'value'), _line_value(row, 'status')])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([[(_tr('print_warehouse'), payload.get('warehouse_name') or payload.get('warehouse') or _tr('all')), (_tr('print_date'), _print_meta_line()), (_tr('print_notes'), payload.get('notes') or '')]])}
    {_table(['#', _tr('print_item'), _tr('print_barcode'), _tr('print_warehouse'), _tr('quantity'), _tr('print_unit'), _tr('inventory_value'), _tr('status')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('inventory_balances_footer'))}
    """
    return base_document(title, body, paper, settings)


def inventory_movements_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_movements")
    payload = dict(data or {})
    rows_data = list(payload.get('rows') or payload.get('movements') or [])
    title = _tr('inventory_movements_report')
    rows: List[List[Any]] = []
    for i, row in enumerate(rows_data, 1):
        rows.append([i, _line_value(row, 'created_at', 'date'), _line_value(row, 'item_name', 'name', default=row.get('item_id', '')), _line_value(row, 'warehouse_name', 'warehouse'), _inventory_movement_type(row.get('movement_type')), _line_value(row, 'quantity'), _line_value(row, 'unit_cost'), _line_value(row, 'reference_type'), _line_value(row, 'notes')])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([[(_tr('print_warehouse'), payload.get('warehouse_name') or payload.get('warehouse') or _tr('all')), (_tr('status'), payload.get('movement_type') or _tr('all')), (_tr('print_date'), _print_meta_line())]])}
    {_table(['#', _tr('print_date'), _tr('print_item'), _tr('print_warehouse'), _tr('type'), _tr('quantity'), _tr('unit_cost'), _tr('reference'), _tr('print_notes')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('inventory_movements_footer'))}
    """
    return base_document(title, body, paper, settings)


def inventory_ledger_html(data: Dict[str, Any], paper: str = "default") -> str:
    settings = _settings()
    paper = _normalize_paper(paper, settings, "inventory_ledger")
    payload = dict(data or {})
    rows_data = list(payload.get('rows') or payload.get('ledger') or [])
    title = _tr('inventory_ledger_report')
    rows: List[List[Any]] = []
    for i, row in enumerate(rows_data, 1):
        rows.append([i, _line_value(row, 'created_at', 'date'), _line_value(row, 'item_name', 'name', default=row.get('item_id', '')), _line_value(row, 'warehouse_name', 'warehouse'), _inventory_movement_type(row.get('movement_type')), _line_value(row, 'direction'), _line_value(row, 'quantity'), _line_value(row, 'unit_cost'), _line_value(row, 'reference_type'), _line_value(row, 'notes')])
    body = f"""
    {_company_header(settings, title)}
    <div class='document-title'>{_s(title)}</div>
    {_meta_table([[(_tr('print_warehouse'), payload.get('warehouse_name') or payload.get('warehouse') or _tr('all')), (_tr('print_date'), _print_meta_line()), (_tr('print_notes'), payload.get('notes') or '')]])}
    {_table(['#', _tr('print_date'), _tr('print_item'), _tr('print_warehouse'), _tr('type'), _tr('direction'), _tr('quantity'), _tr('unit_cost'), _tr('reference'), _tr('print_notes')], rows, _tr('print_no_data'))}
    {_footer(settings, _tr('inventory_ledger_footer'))}
    """
    return base_document(title, body, paper, settings)
