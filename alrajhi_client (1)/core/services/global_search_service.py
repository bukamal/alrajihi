# -*- coding: utf-8 -*-
"""Global search application service.

Phase 56 keeps data access behind existing service/gateway boundaries.  The
shell asks this service for lightweight search hits and then opens matching
Document Tabs.  No SQL or repository access is allowed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class GlobalSearchHit:
    kind: str
    entity_id: int | str | None
    title: str
    subtitle: str = ""
    icon_name: str = "fa5s.search"
    payload: Dict[str, Any] | None = None

    @property
    def key(self) -> str:
        suffix = "new" if self.entity_id is None else str(self.entity_id)
        return f"search:{self.kind}:{suffix}"


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _first(row: Dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return _text(value)
    return default


def _safe_rows(func, *args, **kwargs) -> List[Dict[str, Any]]:
    try:
        result = func(*args, **kwargs)
        if isinstance(result, tuple):
            result = result[0]
        return list(result or [])
    except Exception:
        return []


class GlobalSearchService:
    """Cross-module search facade for the tabbed workspace."""

    def search(self, query: str, limit_per_domain: int = 5) -> List[GlobalSearchHit]:
        query = (query or "").strip()
        if len(query) < 2:
            return []
        limit = max(1, min(int(limit_per_domain or 5), 20))
        hits: List[GlobalSearchHit] = []
        hits.extend(self._items(query, limit))
        hits.extend(self._parties(query, limit))
        hits.extend(self._invoices(query, limit))
        hits.extend(self._vouchers(query, limit))
        hits.extend(self._manufacturing(query, limit))
        return hits[: max(10, limit * 6)]

    def _items(self, query: str, limit: int) -> Iterable[GlobalSearchHit]:
        from core.services.product_service import product_service

        for row in _safe_rows(product_service.items, search=query, limit=limit, offset=0):
            item_id = row.get("id")
            title = _first(row, "name", "item_name", "arabic_name", default=f"Item {item_id}")
            barcode = _first(row, "barcode", "code")
            subtitle = " · ".join(part for part in [barcode, _first(row, "category_name")] if part)
            yield GlobalSearchHit("item", item_id, title, subtitle, "fa5s.box-open")

    def _parties(self, query: str, limit: int) -> Iterable[GlobalSearchHit]:
        from core.services.entity_service import entity_service

        for kind, func, icon in (
            ("customer", entity_service.customers, "fa5s.user-friends"),
            ("supplier", entity_service.suppliers, "fa5s.truck-loading"),
        ):
            for row in _safe_rows(func, search=query, limit=limit, offset=0):
                entity_id = row.get("id")
                title = _first(row, "name", default=f"{kind} {entity_id}")
                subtitle = " · ".join(part for part in [_first(row, "phone"), _first(row, "address")] if part)
                yield GlobalSearchHit(kind, entity_id, title, subtitle, icon)

    def _invoices(self, query: str, limit: int) -> Iterable[GlobalSearchHit]:
        from core.services.invoice_service import invoice_service

        for inv_type, icon in (("sale", "fa5s.file-invoice-dollar"), ("purchase", "fa5s.file-invoice")):
            for row in _safe_rows(invoice_service.list_records, search=query, inv_type=inv_type, limit=limit, offset=0):
                invoice_id = row.get("id")
                ref = _first(row, "reference", "number", default=f"#{invoice_id}")
                total = _first(row, "total", "grand_total")
                party = _first(row, "customer_name", "supplier_name", "party_name")
                title = f"{ref} — {party}" if party else ref
                subtitle = " · ".join(part for part in [inv_type, total, _first(row, "date", "invoice_date")] if part)
                yield GlobalSearchHit("invoice", invoice_id, title, subtitle, icon, {"inv_type": inv_type})

    def _vouchers(self, query: str, limit: int) -> Iterable[GlobalSearchHit]:
        from core.services.voucher_service import voucher_service

        for row in _safe_rows(voucher_service.list_vouchers, search=query, limit=limit, offset=0):
            voucher_id = row.get("id")
            number = _first(row, "number", "reference", default=f"#{voucher_id}")
            amount = _first(row, "amount")
            vtype = _first(row, "type", default="voucher")
            yield GlobalSearchHit("voucher", voucher_id, number, " · ".join(part for part in [vtype, amount] if part), "fa5s.receipt", {"voucher": row, "voucher_type": vtype})

    def _manufacturing(self, query: str, limit: int) -> Iterable[GlobalSearchHit]:
        from core.services.manufacturing_service import manufacturing_service

        needle = query.casefold()
        for row in _safe_rows(manufacturing_service.boms, limit=limit, offset=0):
            label = _first(row, "product_name", "name", "bom_name", default=f"BOM {row.get('id')}")
            if needle in label.casefold() or needle in _text(row.get("id")).casefold():
                yield GlobalSearchHit("bom", row.get("id"), label, "BOM", "fa5s.industry")
        for row in _safe_rows(manufacturing_service.production_orders, limit=limit, offset=0):
            label = _first(row, "reference", "product_name", default=f"Production Order {row.get('id')}")
            if needle in label.casefold() or needle in _text(row.get("id")).casefold():
                yield GlobalSearchHit("production_order", row.get("id"), label, _first(row, "status"), "fa5s.clipboard-list")


global_search_service = GlobalSearchService()
