# -*- coding: utf-8 -*-
"""Barcode generation and validation helpers.

The project supports two practical barcode modes:
- CODE128: flexible text/numeric internal barcodes.
- EAN13: numeric retail barcode with a valid check digit.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Optional


class BarcodeError(ValueError):
    """Raised when a barcode is invalid for the selected symbology."""


@dataclass(frozen=True)
class BarcodeInfo:
    value: str
    symbology: str


class BarcodeService:
    CODE128_PATTERN = re.compile(r"^[A-Za-z0-9._\- /]{1,64}$")

    def normalize(self, barcode: Optional[str]) -> Optional[str]:
        if barcode is None:
            return None
        value = str(barcode).strip()
        return value or None

    def ean13_check_digit(self, first_12_digits: str) -> str:
        digits = re.sub(r"\D", "", str(first_12_digits))
        if len(digits) != 12:
            raise BarcodeError("EAN-13 يحتاج 12 رقمًا لحساب رقم التحقق")
        total = sum(int(d) if i % 2 == 0 else int(d) * 3 for i, d in enumerate(digits))
        return str((10 - (total % 10)) % 10)

    def is_valid_ean13(self, value: str) -> bool:
        value = str(value or '').strip()
        return bool(re.fullmatch(r"\d{13}", value)) and self.ean13_check_digit(value[:12]) == value[-1]

    def generate_ean13(self, prefix: str = "290") -> str:
        """Generate a valid internal-use EAN-13 barcode.

        Prefix 290 is commonly used as an internal/private range in many POS
        workflows; it is not a GS1 allocation guarantee.
        """
        prefix_digits = re.sub(r"\D", "", prefix)[:6] or "290"
        body_len = 12 - len(prefix_digits)
        body = ''.join(str(random.randint(0, 9)) for _ in range(body_len))
        first12 = prefix_digits + body
        return first12 + self.ean13_check_digit(first12)

    def generate_code128(self, prefix: str = "ITM") -> str:
        serial = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(10))
        return f"{prefix}-{serial}"

    def detect_symbology(self, barcode: Optional[str]) -> str:
        value = self.normalize(barcode)
        if not value:
            return "EMPTY"
        if re.fullmatch(r"\d{13}", value):
            return "EAN13" if self.is_valid_ean13(value) else "INVALID_EAN13"
        return "CODE128" if self.CODE128_PATTERN.fullmatch(value) else "INVALID"

    def validate(self, barcode: Optional[str], *, allow_empty: bool = True) -> Optional[BarcodeInfo]:
        value = self.normalize(barcode)
        if not value:
            if allow_empty:
                return None
            raise BarcodeError("الباركود مطلوب")
        sym = self.detect_symbology(value)
        if sym == "INVALID_EAN13":
            raise BarcodeError("باركود EAN-13 غير صالح: رقم التحقق غير صحيح")
        if sym == "INVALID":
            raise BarcodeError("صيغة الباركود غير صالحة. استخدم EAN-13 رقمي أو Code128 بحروف/أرقام ورموز بسيطة")
        return BarcodeInfo(value=value, symbology=sym)


barcode_service = BarcodeService()
