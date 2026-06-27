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
_LAST_TEMPLATE_LOAD_ERROR = ""


def _boolish(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "نعم", "ja"}


def _printing_setting(key: str, default: Any = None) -> Any:
    """Read printing policy through SettingsService/SettingsGateway.

    This keeps template diagnostics and emergency fallback behavior consistent in
    local and client/server modes.  The loader must stay defensive because it is
    used precisely when the regular printing module import path may be broken.
    """
    try:
        from core.services.settings_service import settings_service
        cfg = settings_service.get_printing_settings()
        if isinstance(cfg, dict) and key in cfg:
            return cfg.get(key)
        return settings_service.get(f"printing/{key}", default)
    except Exception:
        return default


def _allow_emergency_fallback() -> bool:
    if _boolish(os.environ.get("ALRAJHI_PRINT_ALLOW_EMERGENCY_FALLBACK"), False):
        return True
    if _boolish(os.environ.get("ALRAJHI_PRINT_STRICT_TEMPLATES"), False):
        return False
    return _boolish(_printing_setting("allow_emergency_fallback", False), False)


def _show_template_diagnostics() -> bool:
    return _boolish(_printing_setting("show_template_diagnostics", True), True)


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
    executable_dir = os.path.dirname(getattr(sys, "executable", "") or "")
    bases = [
        here,
        cwd,
        frozen_root,
        os.path.join(frozen_root, "_internal") if frozen_root else "",
        executable_dir,
        os.path.join(executable_dir, "_internal") if executable_dir else "",
    ]
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
            globals()["_LAST_TEMPLATE_LOAD_ERROR"] = f"{name}: {type(exc).__name__}: {exc}"
            continue
        except Exception as exc:
            globals()["_LAST_TEMPLATE_LOAD_ERROR"] = f"{name}: {type(exc).__name__}: {exc}"
            continue

    for candidate in _candidate_template_files():
        try:
            module = _load_module_from_file(candidate)
            if module is not None:
                _REAL_MODULE = module
                return module
        except Exception as exc:
            globals()["_LAST_TEMPLATE_LOAD_ERROR"] = f"{candidate}: {type(exc).__name__}: {exc}"
            continue
    return None


def _fallback_language_direction() -> tuple[str, str]:
    try:
        from i18n.translator import normalize_language, language_direction
        try:
            from core.services.settings_service import settings_service
            lang = normalize_language(settings_service.print_language())
        except Exception:
            lang = normalize_language(None)
        return lang, language_direction(lang)
    except Exception:
        return "ar", "rtl"


def _fallback_text(key: str) -> str:
    lang, _direction = _fallback_language_direction()
    labels = {
        'ar': {
            'item': 'المادة', 'quantity': 'الكمية', 'unit': 'الوحدة', 'price': 'السعر', 'discount': 'الخصم', 'tax': 'الضريبة', 'total': 'الإجمالي',
            'no_lines': 'لا توجد بنود', 'subtotal': 'الإجمالي قبل الخصم', 'paid': 'المقبوض', 'refunded': 'المردود', 'remaining': 'المتبقي',
            'invoice': 'فاتورة', 'sales_invoice': 'فاتورة مبيعات', 'purchase_invoice': 'فاتورة مشتريات', 'sales_return': 'مرتجع بيع', 'purchase_return': 'مرتجع شراء',
            'data': 'البيانات', 'number': 'الرقم', 'date': 'التاريخ', 'party': 'الطرف', 'warehouse': 'المستودع', 'payment': 'طريقة الدفع', 'currency': 'العملة',
            'original_invoice': 'الفاتورة الأصلية', 'status': 'الحالة', 'user': 'المستخدم', 'notes': 'ملاحظات', 'report': 'تقرير', 'no_data': 'لا توجد بيانات', 'template_error_title': 'تعذر تحميل قالب الطباعة', 'template_error_message': 'لم يتم إنشاء مستند الطباعة لأن القالب الحقيقي غير متاح.', 'template_error_hint': 'راجع تضمين print_templates.py في الحزمة أو فعّل قالب الطوارئ مؤقتًا من إعدادات الطباعة.', 'template_error_detail': 'تفاصيل الخطأ',
        },
        'de': {
            'item': 'Artikel', 'quantity': 'Menge', 'unit': 'Einheit', 'price': 'Preis', 'discount': 'Rabatt', 'tax': 'Steuer', 'total': 'Gesamt',
            'no_lines': 'Keine Positionen', 'subtotal': 'Zwischensumme', 'paid': 'Bezahlt', 'refunded': 'Erstattet', 'remaining': 'Restbetrag',
            'invoice': 'Rechnung', 'sales_invoice': 'Verkaufsrechnung', 'purchase_invoice': 'Einkaufsrechnung', 'sales_return': 'Verkaufsretoure', 'purchase_return': 'Einkaufsretoure',
            'data': 'Daten', 'number': 'Nummer', 'date': 'Datum', 'party': 'Partei', 'warehouse': 'Lager', 'payment': 'Zahlungsart', 'currency': 'Währung',
            'original_invoice': 'Ursprungsrechnung', 'status': 'Status', 'user': 'Benutzer', 'notes': 'Notizen', 'report': 'Bericht', 'no_data': 'Keine Daten', 'template_error_title': 'Druckvorlage konnte nicht geladen werden', 'template_error_message': 'Das Druckdokument wurde nicht erstellt, weil die echte Vorlage nicht verfügbar ist.', 'template_error_hint': 'Prüfen Sie die Einbindung von print_templates.py oder aktivieren Sie die Notfallvorlage temporär in den Druckeinstellungen.', 'template_error_detail': 'Fehlerdetails',
        },
        'en': {
            'item': 'Item', 'quantity': 'Quantity', 'unit': 'Unit', 'price': 'Price', 'discount': 'Discount', 'tax': 'Tax', 'total': 'Total',
            'no_lines': 'No lines', 'subtotal': 'Subtotal', 'paid': 'Paid', 'refunded': 'Refunded', 'remaining': 'Remaining',
            'invoice': 'Invoice', 'sales_invoice': 'Sales invoice', 'purchase_invoice': 'Purchase invoice', 'sales_return': 'Sales return', 'purchase_return': 'Purchase return',
            'data': 'Data', 'number': 'Number', 'date': 'Date', 'party': 'Party', 'warehouse': 'Warehouse', 'payment': 'Payment method', 'currency': 'Currency',
            'original_invoice': 'Original invoice', 'status': 'Status', 'user': 'User', 'notes': 'Notes', 'report': 'Report', 'no_data': 'No data', 'template_error_title': 'Print template could not be loaded', 'template_error_message': 'The print document was not generated because the real template is unavailable.', 'template_error_hint': 'Check print_templates.py packaging or temporarily enable the emergency template in print settings.', 'template_error_detail': 'Error detail',
        },
        'fr': {
            'item': 'Article', 'quantity': 'Quantité', 'unit': 'Unité', 'price': 'Prix', 'discount': 'Remise', 'tax': 'Taxe', 'total': 'Total',
            'no_lines': 'Aucune ligne', 'subtotal': 'Sous-total', 'paid': 'Payé', 'refunded': 'Remboursé', 'remaining': 'Restant',
            'invoice': 'Facture', 'sales_invoice': 'Facture de vente', 'purchase_invoice': 'Facture d’achat', 'sales_return': 'Retour de vente', 'purchase_return': 'Retour d’achat',
            'data': 'Données', 'number': 'Numéro', 'date': 'Date', 'party': 'Tiers', 'warehouse': 'Entrepôt', 'payment': 'Mode de paiement', 'currency': 'Devise',
            'original_invoice': 'Facture d’origine', 'status': 'Statut', 'user': 'Utilisateur', 'notes': 'Notes', 'report': 'Rapport', 'no_data': 'Aucune donnée', 'template_error_title': "Le modèle d’impression n’a pas pu être chargé", 'template_error_message': "Le document d’impression n’a pas été généré car le modèle réel est indisponible.", 'template_error_hint': "Vérifiez l’intégration de print_templates.py ou activez temporairement le modèle de secours dans les paramètres d’impression.", 'template_error_detail': 'Détail de l’erreur',
        },
    }
    return labels.get(lang, labels['ar']).get(key, labels['ar'].get(key, key))


def _html_doc(title: str, body: str, *, emergency: bool = False) -> str:
    safe_title = html.escape(str(title or ""))
    lang, direction = _fallback_language_direction()
    align = "right" if direction == "rtl" else "left"
    error_comment = html.escape(_LAST_TEMPLATE_LOAD_ERROR or "unknown template loading error")
    warning = ""
    if emergency and _show_template_diagnostics():
        warning = (
            "<div class='fallback-warning'><b>Emergency print template used.</b><br>"
            f"{error_comment}</div>"
        )
    return (
        f"<!doctype html><html lang='{lang}' dir='{direction}'><head><meta charset='utf-8'>"
        f"<title>{safe_title}</title>"
        f"<style>body{{font-family:Tahoma,Arial,sans-serif;margin:24px;direction:{direction};color:#111827;}}"
        "h1{font-size:22px;text-align:center;margin:0 0 16px;}"
        "table{width:100%;border-collapse:collapse;margin-top:12px;table-layout:fixed;}"
        "th{background:#1d4ed8;color:white;font-weight:700;}"
        "th,td{border:1px solid #dbe3ef;padding:7px;text-align:center;word-wrap:break-word;}"
        "tr:nth-child(even) td{background:#f8fafc;}"
        ".muted{color:#64748b;text-align:center;margin:8px 0;}"
        f".fallback-warning{{direction:ltr;text-align:{align};font-size:11px;color:#b91c1c;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px;margin-bottom:12px;}}"
        "</style></head><body>"
        f"<!-- fallback-print-template: {error_comment} -->"
        f"{warning}<h1>{safe_title}</h1>{body}</body></html>"
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
    headers = [_fallback_text("item"), _fallback_text("quantity"), _fallback_text("unit"), _fallback_text("price"), _fallback_text("discount"), _fallback_text("tax"), _fallback_text("total")]
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
        rows.append([_fallback_text("no_lines"), "", "", "", "", "", ""])
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
        (_fallback_text("subtotal"), _money(_get(data, "total_before_discount", "subtotal"))),
        (_fallback_text("discount"), _money(_get(data, "discount_amount", "discount"))),
        (_fallback_text("tax"), _money(_get(data, "tax_amount", "tax"))),
        (_fallback_text("total"), _money(_get(data, "total", "refund_amount" if is_return else "total"))),
        (_fallback_text("paid") if not is_return else _fallback_text("refunded"), _money(_get(data, "paid_amount", "paid", "refund_amount"))),
        (_fallback_text("remaining"), _money(_get(data, "remaining"))),
    ]
    body = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in rows)
    return f"<table><tbody>{body}</tbody></table>"


def _fallback_invoice_template(data: Any, *, is_return: bool = False) -> str:
    if not isinstance(data, dict):
        return _fallback_report_template(_fallback_text("invoice"), [[_clean_value(data)]], [_fallback_text("data")])
    doc_type = _get(data, "return_type", "type")
    if is_return:
        title = _fallback_text("sales_return") if str(doc_type) in {"sale", "sale_return"} else _fallback_text("purchase_return")
    else:
        title = _fallback_text("sales_invoice") if str(doc_type) == "sale" else _fallback_text("purchase_invoice") if str(doc_type) == "purchase" else _fallback_text("invoice")
    ref = _get(data, "reference", "return_number", "return_no", "number", "id")
    party = _get(data, "party_name", "customer_name", "supplier_name", "entity_name")
    party_label = _fallback_text("party")
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
      <div class='section'><b>{notes_label}:</b> {notes}</div>
    </div>
    """.format(
        title=html.escape(title),
        meta=_fallback_meta_table([
            [(_fallback_text("number"), ref), (_fallback_text("date"), _get(data, "date", "created_at")), (party_label, party)],
            [(_fallback_text("warehouse"), _get(data, "warehouse_name", "warehouse")), (_fallback_text("payment"), _get(data, "payment_method")), (_fallback_text("currency"), _get(data, "currency", "original_currency"))],
            [(_fallback_text("original_invoice"), _get(data, "original_invoice", "original_invoice_id")), (_fallback_text("status"), _get(data, "payment_status", "status")), (_fallback_text("user"), _get(data, "user_name", "created_by"))],
        ]),
        lines=_fallback_lines_table(_get(data, "lines", default=[])),
        totals=_fallback_totals_table(data, is_return=is_return),
        notes=html.escape(_clean_value(_get(data, "notes", "description"))),
        notes_label=html.escape(_fallback_text("notes")),
    )
    return _html_doc(title, body, emergency=True)

def _fallback_report_template(*args: Any, **kwargs: Any) -> str:
    title = kwargs.get("title") if "title" in kwargs else (args[0] if len(args) > 0 else _fallback_text("report"))
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
        no_data_text = html.escape(_fallback_text("no_data"))
        body_rows.append(f"<tr><td colspan='{colspan}'>{no_data_text}</td></tr>")
    table = f"<div class='muted'>{html.escape(str(subtitle or ''))}</div><table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
    return _html_doc(str(title or _fallback_text("report")), table, emergency=True)


def _template_error_document(name: str, *args: Any, **kwargs: Any) -> str:
    """Return a visible browser HTML error instead of silently printing weak output.

    By default a missing real template is a blocking print error.  The emergency
    renderer can still be enabled through printing/allow_emergency_fallback for
    field troubleshooting, but it is no longer the silent default.
    """
    lang, direction = _fallback_language_direction()
    title = _fallback_text("template_error_title")
    message = _fallback_text("template_error_message")
    hint = _fallback_text("template_error_hint")
    detail_label = _fallback_text("template_error_detail")
    detail = html.escape(_LAST_TEMPLATE_LOAD_ERROR or f"Missing callable: {name}")
    detail_block = ""
    if _show_template_diagnostics():
        detail_block = f"<h2>{html.escape(detail_label)}</h2><pre>{detail}</pre>"
    body = f"""
    <main class='print-template-error'>
      <section class='error-card'>
        <div class='error-code'>PRINT-TEMPLATE-UNAVAILABLE</div>
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(message)}</p>
        <p class='hint'>{html.escape(hint)}</p>
        <dl>
          <dt>template</dt><dd>{html.escape(name)}</dd>
          <dt>language</dt><dd>{html.escape(lang)}</dd>
          <dt>direction</dt><dd>{html.escape(direction)}</dd>
        </dl>
        {detail_block}
      </section>
    </main>
    """
    css = """
    <style>
      body{margin:0;background:#f8fafc;color:#111827;font-family:Tahoma,Arial,sans-serif;}
      .print-template-error{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:28px;}
      .error-card{max-width:820px;width:100%;background:#fff;border:2px solid #fecaca;border-radius:16px;padding:24px;box-shadow:0 14px 40px rgba(15,23,42,.12);}
      .error-code{display:inline-block;background:#fee2e2;color:#991b1b;border-radius:999px;padding:5px 12px;font-weight:800;font-size:12px;letter-spacing:.04em;}
      h1{font-size:24px;margin:14px 0 8px;color:#991b1b;}
      h2{font-size:15px;margin-top:18px;}
      p{line-height:1.8;margin:8px 0;}
      .hint{color:#475569;}
      dl{display:grid;grid-template-columns:140px 1fr;gap:6px 12px;margin-top:16px;}
      dt{font-weight:800;color:#475569;}
      dd{margin:0;}
      pre{white-space:pre-wrap;direction:ltr;text-align:left;background:#0f172a;color:#e2e8f0;border-radius:10px;padding:12px;font-size:12px;overflow:auto;}
      @media print{body{background:#fff}.error-card{box-shadow:none}}
    </style>
    """
    return f"<!doctype html><html lang='{lang}' dir='{direction}'><head><meta charset='utf-8'><title>{html.escape(title)}</title>{css}</head><body>{body}</body></html>"


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
            return _html_doc(str(title), table, emergency=True)
        body = f"<div style='border:1px solid #dbe3ef;padding:12px'>{html.escape(_clean_value(payload))}</div>"
        return _html_doc(str(title), body, emergency=True)
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
        if _allow_emergency_fallback():
            return fallback(*args, **kwargs)
        return _template_error_document(name, *args, **kwargs)

    return _render
