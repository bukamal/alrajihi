# -*- coding: utf-8 -*-
"""Dashboard aggregation service.

The dashboard should render data, not calculate business indicators itself.  This
service centralizes KPI, chart, and recent-activity data so the widget stays thin
and later caching/optimization can be implemented in one place.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from core.services.reporting_service import reporting_service
from core.services.expense_service import expense_service


class DashboardService:
    CACHE_TTL_SECONDS = 30

    def __init__(self):
        self._cache: Dict[str, object] = {}
        self._cache_time: datetime | None = None

    def clear_cache(self) -> None:
        self._cache = {}
        self._cache_time = None

    def _fresh(self) -> bool:
        if not self._cache_time:
            return False
        return (datetime.now() - self._cache_time).total_seconds() <= self.CACHE_TTL_SECONDS

    def snapshot(self, use_cache: bool = True) -> Dict:
        if use_cache and self._fresh() and self._cache:
            return self._cache
        data = {
            'summary': self.summary(),
            'monthly_trend': self.monthly_trend(),
            'recent_entries': self.recent_entries(limit=5),
        }
        self._cache = data
        self._cache_time = datetime.now()
        return data

    def summary(self) -> Dict:
        summary = reporting_service.summary()
        if not isinstance(summary, dict):
            summary = {}
        keys = ('cash_balance', 'total_sales', 'total_purchases', 'total_expenses',
                'receivables', 'payables', 'net_profit')
        return {k: self._decimal(summary.get(k, 0)) for k in keys}

    def monthly_trend(self, months_count: int = 6) -> List[Dict]:
        expenses = expense_service.all()
        monthly_in = defaultdict(lambda: Decimal('0'))
        monthly_out = defaultdict(lambda: Decimal('0'))
        for row in expenses:
            date_str = str(row.get('expense_date', '') or '')
            if len(date_str) < 7:
                continue
            month_key = date_str[:7]
            amount = self._decimal(row.get('amount', 0))
            if row.get('type') == 'incoming':
                monthly_in[month_key] += amount
            else:
                monthly_out[month_key] += amount

        today = datetime.now()
        result = []
        # Calendar-month precision is not required here; using 30-day steps keeps
        # the legacy behavior while centralizing it away from the widget.
        for i in range(months_count - 1, -1, -1):
            d = today - timedelta(days=30 * i)
            key = d.strftime('%Y-%m')
            result.append({
                'month_key': key,
                'label': key[5:7] + '/' + key[2:4],
                'incoming': monthly_in.get(key, Decimal('0')),
                'outgoing': monthly_out.get(key, Decimal('0')),
            })
        return result

    def recent_entries(self, limit: int = 5) -> List[Dict]:
        result = []
        for row in expense_service.recent(limit=limit):
            result.append({
                'date': row.get('expense_date', ''),
                'company': row.get('company_name', ''),
                'amount': self._decimal(row.get('amount', 0)),
                'type': 'وارد' if row.get('type') == 'incoming' else 'صادر',
            })
        return result

    def _decimal(self, value) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except Exception:
            return Decimal('0')


dashboard_service = DashboardService()
