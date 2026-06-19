from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List

from PyQt5.QtWidgets import QMessageBox

from ..i18n import tr


class TransactionPrintingBridge:
    """Printing/export adapter for unified transaction documents.

    The transaction document tab owns UI state and persistence.  This adapter
    converts that state into the stable payload shape consumed by
    printing.printing_service.  It intentionally lives under features/
    transactions so invoice_dialog.py remains a legacy fallback instead of the
    owner of document output.
    """

    def __init__(self, host):
        self.host = host

    def preview(self) -> None:
        payload = self._payload()
        if not payload:
            return
        return self.print()

    def print(self) -> bool:
        payload = self._payload()
        if not payload:
            return False
        return bool(self._service_call("return_print" if self.host.is_return else "invoice_print", payload))

    def browser(self) -> bool:
        payload = self._payload()
        if not payload:
            return False
        return self.print()

    def pdf(self) -> bool:
        # Phase 235: legacy callers that still ask for PDF use the unified print route.
        return self.print()

    def _service_call(self, method_name: str, payload: Dict[str, Any]):
        try:
            from printing.printing_service import printing_service
            method = getattr(printing_service, method_name)
            return method(payload, self.host)
        except Exception as exc:
            QMessageBox.warning(self.host, tr("printing"), str(exc))
            return False

    def _payload(self) -> Dict[str, Any]:
        if self.host.is_return:
            return self._return_payload()
        return self._invoice_payload()

    def _invoice_payload(self) -> Dict[str, Any]:
        party_name = self._current_text(self.host.party_combo, ignore=(tr("transaction_no_party"),))
        warehouse_name = self._current_text(self.host.warehouse_combo)
        total = self.host.lines_model.total_amount()
        paid = self.host.totals_panel.paid_amount()
        lines = self._invoice_lines()
        return {
            "id": self.host.invoice_id,
            "type": self.host.inv_type,
            "reference": self.host.ref_edit.text().strip(),
            "date": self.host.date_edit.date().toString("yyyy-MM-dd"),
            "customer_id": self.host._selected_party_id() if self.host.inv_type == "sale" else None,
            "supplier_id": self.host._selected_party_id() if self.host.inv_type == "purchase" else None,
            "party_name": party_name,
            "customer_name": party_name if self.host.inv_type == "sale" else "",
            "supplier_name": party_name if self.host.inv_type == "purchase" else "",
            "warehouse_id": self.host._selected_warehouse_id(),
            "warehouse_name": warehouse_name,
            "payment_method": self.host.totals_panel.payment_method(),
            "payment_status": "paid" if paid >= total and total > 0 else ("partial" if paid > 0 else "unpaid"),
            "subtotal": self.host.lines_model.subtotal_amount(),
            "total_before_discount": self.host.lines_model.subtotal_amount(),
            "discount_amount": self.host.lines_model.discount_amount(),
            "tax_amount": self.host.lines_model.tax_amount(),
            "total": total,
            "paid": paid,
            "paid_amount": paid,
            "remaining": total - paid,
            "notes": self.host.notes.toPlainText().strip(),
            "currency": getattr(self.host, "display_currency", None),
            "original_currency": getattr(self.host, "display_currency", None),
            "exchange_rate_to_usd": self._exchange_rate_to_usd(),
            "lines": lines,
        }

    def _return_payload(self) -> Dict[str, Any]:
        original_invoice_text = self._current_text(self.host.original_invoice_combo, ignore=(tr("transaction_choose_original_invoice"),))
        party_name = self._current_text(self.host.party_combo, ignore=(tr("transaction_no_party"),))
        warehouse_name = self._current_text(self.host.warehouse_combo)
        total = self.host.lines_model.total_amount()
        refund = self.host.totals_panel.paid_amount()
        return_no = self.host.ref_edit.text().strip()
        return {
            "id": self.host.return_id or self.host.invoice_id,
            "type": "sale" if self.host.inv_type == "sale" else "purchase",
            "return_type": "sale_return" if self.host.inv_type == "sale" else "purchase_return",
            "reference": return_no,
            "return_number": return_no,
            "return_no": return_no,
            "original_invoice_id": self.host._selected_original_invoice_id(),
            "original_invoice": original_invoice_text,
            "date": self.host.date_edit.date().toString("yyyy-MM-dd"),
            "party_name": party_name,
            "customer_name": party_name if self.host.inv_type == "sale" else "",
            "supplier_name": party_name if self.host.inv_type == "purchase" else "",
            "warehouse_id": self.host._selected_warehouse_id(),
            "warehouse_name": warehouse_name,
            "payment_method": self.host._service_return_payment_method(),
            "refund_amount": refund,
            "subtotal": total,
            "total_before_discount": total,
            "discount_amount": Decimal("0"),
            "tax_amount": Decimal("0"),
            "total": total,
            "paid": refund,
            "paid_amount": refund,
            "remaining": total - refund,
            "notes": self.host.notes.toPlainText().strip(),
            "currency": getattr(self.host, "display_currency", None),
            "original_currency": getattr(self.host, "display_currency", None),
            "exchange_rate_to_usd": self._exchange_rate_to_usd(),
            "lines": self._return_lines(),
        }

    def _invoice_lines(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for row in self.host.lines_model.lines:
            if not row.get("item_id"):
                continue
            qty = self._decimal(row.get("qty"))
            if qty <= 0:
                continue
            price = self._decimal(row.get("price") or row.get("cost"))
            result.append({
                "item_id": row.get("item_id"),
                "item_name": row.get("item", ""),
                "name": row.get("item", ""),
                "barcode": row.get("barcode", ""),
                "unit": row.get("unit", ""),
                "unit_id": row.get("unit_id"),
                "quantity": qty,
                "qty": qty,
                "unit_price": price,
                "price": price,
                "discount": self._decimal(row.get("discount")),
                "discount_percent": self._decimal(row.get("discount")),
                "tax": self._decimal(row.get("tax")),
                "tax_percent": self._decimal(row.get("tax")),
                "line_total": self._decimal(row.get("total")),
                "total": self._decimal(row.get("total")),
                "description": row.get("notes", ""),
                "notes": row.get("notes", ""),
                "batch": row.get("batch", ""),
                "expiry": row.get("expiry", ""),
            })
        return result

    def _return_lines(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for row in self.host.lines_model.lines:
            if not row.get("item_id") or not row.get("original_invoice_line_id"):
                continue
            qty = self._decimal(row.get("qty"))
            if qty <= 0:
                continue
            price = self._decimal(row.get("price") or row.get("cost"))
            result.append({
                "original_invoice_line_id": row.get("original_invoice_line_id"),
                "item_id": row.get("item_id"),
                "item_name": row.get("item", ""),
                "name": row.get("item", ""),
                "barcode": row.get("barcode", ""),
                "unit": row.get("unit", ""),
                "unit_id": row.get("unit_id"),
                "quantity": qty,
                "qty": qty,
                "unit_price": price,
                "price": price,
                "line_total": self._decimal(row.get("total")),
                "total": self._decimal(row.get("total")),
                "discount": Decimal("0"),
                "discount_percent": Decimal("0"),
                "tax": Decimal("0"),
                "tax_percent": Decimal("0"),
                "reason": row.get("reason") or "",
                "description": row.get("notes") or row.get("reason") or "",
                "notes": row.get("notes") or row.get("reason") or "",
                "restock": row.get("restock") or "",
                "conversion_factor": row.get("conversion_factor"),
                "quantity_in_base": self._decimal(row.get("qty")) * self._decimal(row.get("conversion_factor") or 1),
            })
        return result

    def _current_text(self, combo, ignore: Iterable[str] = ()) -> str:
        text = (combo.currentText() or "").strip()
        return "" if text in set(ignore) else text

    def _exchange_rate_to_usd(self) -> float:
        try:
            return float(self.host._exchange_rate_to_usd())
        except Exception:
            return 1.0

    def _decimal(self, value) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except Exception:
            return Decimal("0")
