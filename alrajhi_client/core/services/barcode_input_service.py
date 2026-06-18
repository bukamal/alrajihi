# -*- coding: utf-8 -*-
from __future__ import annotations

"""Unified barcode input pipeline for transaction/POS-like entry fields.

USB barcode scanners normally behave like keyboards and press Enter after the
code.  A transaction screen must not treat a failed barcode scan as a loose
text search and silently add the first matching material.  This service keeps
barcode scan mode and manual search mode separate while still allowing manual
search by material name/code.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, Optional

from core.services.barcode_service import barcode_service
from core.services.product_service import product_service
from core.services.catalog_service import catalog_service
from core.services.settings_service import settings_service


@dataclass(frozen=True)
class BarcodeInputResult:
    item: Optional[Dict[str, Any]]
    normalized: str = ""
    mode: str = "manual"
    message_key: str = ""

    @property
    def found(self) -> bool:
        return self.item is not None

    @property
    def is_scan(self) -> bool:
        return self.mode == "scan"


class BarcodeInputService:
    """Read material input consistently across invoices, returns, POS and camera scan."""

    CONTROL_CHARS = "\r\n\t\x00"

    def scanner_settings(self) -> Dict[str, Any]:
        return {
            "prefix": settings_service.get("barcode/scanner/prefix", "") or "",
            "suffix": settings_service.get("barcode/scanner/suffix", "") or "",
            "min_scan_length": int(settings_service.get("barcode/scanner/min_length", "6") or 6),
            "numeric_scan_is_exact": str(settings_service.get("barcode/scanner/numeric_exact", "true")).lower() == "true",
        }

    def normalize(self, raw: Any) -> str:
        value = "" if raw is None else str(raw)
        value = value.strip(self.CONTROL_CHARS + " ")
        settings = self.scanner_settings()
        prefix = str(settings.get("prefix") or "")
        suffix = str(settings.get("suffix") or "")
        if prefix and value.startswith(prefix):
            value = value[len(prefix):]
        if suffix and value.endswith(suffix):
            value = value[:-len(suffix)]
        return (barcode_service.normalize(value) or "").strip()

    def looks_like_scan(self, normalized: str) -> bool:
        if not normalized:
            return False
        settings = self.scanner_settings()
        min_len = int(settings.get("min_scan_length") or 6)
        if barcode_service.detect_symbology(normalized) in {"EAN13", "CODE128"} and len(normalized) >= min_len:
            if " " not in normalized:
                return True
        if bool(settings.get("numeric_scan_is_exact")) and re.fullmatch(r"\d{%d,}" % min_len, normalized):
            return True
        return False

    def lookup_scan(self, raw: Any) -> BarcodeInputResult:
        normalized = self.normalize(raw)
        if not normalized:
            return BarcodeInputResult(None, normalized, "scan", "transaction_barcode_empty")
        item = product_service.item_by_barcode(normalized)
        if item:
            return BarcodeInputResult(item, normalized, "scan", "")
        return BarcodeInputResult(None, normalized, "scan", "transaction_barcode_not_found")

    def _text_key(self, value: Any) -> str:
        return str(value or "").strip().casefold()

    def _manual_exact_name_matches(self, rows: list[Dict[str, Any]], normalized: str) -> list[Dict[str, Any]]:
        needle = self._text_key(normalized)
        if not needle:
            return []
        matches = []
        for row in rows or []:
            names = (
                row.get("name"),
                row.get("item_name"),
                row.get("product_name"),
                row.get("description"),
            )
            if any(self._text_key(value) == needle for value in names):
                matches.append(row)
        return matches

    def lookup_manual(self, raw: Any) -> BarcodeInputResult:
        normalized = self.normalize(raw)
        if not normalized:
            return BarcodeInputResult(None, normalized, "manual", "transaction_search_empty")
        item = product_service.item_by_barcode(normalized)
        if item:
            return BarcodeInputResult(item, normalized, "manual", "")
        rows = catalog_service.items(search=normalized, limit=10) or []
        if len(rows) == 1:
            return BarcodeInputResult(rows[0], normalized, "manual", "")
        exact_name_matches = self._manual_exact_name_matches(rows, normalized)
        if len(exact_name_matches) == 1:
            return BarcodeInputResult(exact_name_matches[0], normalized, "manual", "")
        if len(rows) > 1:
            return BarcodeInputResult(None, normalized, "manual", "transaction_search_ambiguous")
        return BarcodeInputResult(None, normalized, "manual", "transaction_item_not_found")

    def lookup_entry(self, raw: Any, *, mode: str = "auto") -> BarcodeInputResult:
        normalized = self.normalize(raw)
        if mode == "scan" or (mode == "auto" and self.looks_like_scan(normalized)):
            return self.lookup_scan(normalized)
        return self.lookup_manual(normalized)


barcode_input_service = BarcodeInputService()
