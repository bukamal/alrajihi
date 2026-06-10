# -*- coding: utf-8 -*-
"""Camera barcode/QR decoding helpers.

This module is intentionally optional-dependency friendly.  The application can
run without OpenCV/pyzbar; camera scanning simply reports that it is unavailable.
USB barcode scanners continue to work as keyboard input regardless of this
module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class ScanResult:
    value: str
    symbology: str


class BarcodeScannerService:
    SUPPORTED_TYPES = {"EAN13", "EAN8", "CODE128", "QRCODE", "QR-CODE", "QR"}

    def __init__(self) -> None:
        self._cv2 = None
        self._decode = None
        self._load_error: Optional[str] = None
        self._load_optional_dependencies()

    def _load_optional_dependencies(self) -> None:
        try:
            import cv2  # type: ignore
            from pyzbar.pyzbar import decode  # type: ignore
            self._cv2 = cv2
            self._decode = decode
            self._load_error = None
        except Exception as exc:  # pragma: no cover - depends on runtime packages
            self._cv2 = None
            self._decode = None
            self._load_error = str(exc)

    @property
    def cv2(self):
        return self._cv2

    def is_available(self) -> bool:
        return self._cv2 is not None and self._decode is not None

    def unavailable_reason(self) -> str:
        if self.is_available():
            return ""
        return self._load_error or "مكتبات الكاميرا غير متاحة"

    def normalize_type(self, raw_type: Any) -> str:
        text = str(raw_type or '').upper().replace('_', '-').strip()
        if text in ('QRCODE', 'QR-CODE'):
            return 'QR'
        return text or 'UNKNOWN'

    def decode_frame(self, frame: Any) -> List[ScanResult]:
        """Decode all supported barcodes/QR values from an OpenCV frame."""
        if not self.is_available() or frame is None:
            return []
        results: List[ScanResult] = []
        for obj in self._decode(frame):
            try:
                value = obj.data.decode('utf-8').strip()
            except Exception:
                value = str(obj.data or '').strip()
            if not value:
                continue
            sym = self.normalize_type(getattr(obj, 'type', 'UNKNOWN'))
            results.append(ScanResult(value=value, symbology=sym))
        return results

    def first_result(self, frame: Any) -> Optional[ScanResult]:
        decoded = self.decode_frame(frame)
        return decoded[0] if decoded else None

    def open_camera(self, index: int = 0):
        """Return cv2.VideoCapture or None when camera support is unavailable."""
        if not self.is_available():
            return None
        return self._cv2.VideoCapture(index)


barcode_scanner_service = BarcodeScannerService()
