# -*- coding: utf-8 -*-
OFFLINE_READ_MARKERS = (
    "No connection and this operation cannot be queued safely",
    "Connection refused",
    "Max retries exceeded",
    "Failed to establish a new connection",
    "Network is unreachable",
    "Name or service not known",
    "Read timed out",
    "ConnectTimeout",
    "ConnectionError",
)

def is_offline_read_error(exc) -> bool:
    text = str(exc)
    return any(marker in text for marker in OFFLINE_READ_MARKERS)

def offline_read_message(context="البيانات") -> str:
    return f"تعذر تحديث {context} لأن الخادم غير متصل. العمليات المحفوظة Offline ستبقى في قائمة المزامنة."
