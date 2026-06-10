# -*- coding: utf-8 -*-
"""
Compatibility helpers for DAO/Repository return contracts.

Some legacy widgets expect a plain list[dict], while paginated widgets expect
(list[dict], total). These helpers centralize normalization so dialogs do not
break when a DAO returns tuple/dict/list shapes.
"""
from typing import Any, Dict, List, Tuple


def records(result: Any, key: str | None = None) -> List[Dict]:
    """Return a clean list of dictionaries from tuple/dict/list DAO results."""
    if isinstance(result, tuple):
        data = result[0] if result else []
    elif isinstance(result, dict):
        data = []
        for candidate in (key, 'items', 'customers', 'suppliers', 'data', 'rows', 'results'):
            if candidate and isinstance(result.get(candidate), list):
                data = result.get(candidate) or []
                break
    else:
        data = result or []

    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        data = data[0]
    return [x for x in (data or []) if isinstance(x, dict)]


def pair(result: Any, key: str | None = None) -> Tuple[List[Dict], int]:
    """Return (records, total) from any supported DAO result shape."""
    if isinstance(result, tuple):
        recs = records(result, key)
        try:
            total = int(result[1])
        except Exception:
            total = len(recs)
        return recs, total
    recs = records(result, key)
    if isinstance(result, dict):
        for total_key in ('total', 'count', 'total_count'):
            if total_key in result:
                try:
                    return recs, int(result[total_key])
                except Exception:
                    break
    return recs, len(recs)
