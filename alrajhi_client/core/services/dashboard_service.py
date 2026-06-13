# -*- coding: utf-8 -*-
"""Dashboard aggregation service.

The dashboard should render data, not calculate business indicators itself.  This
service centralizes KPI, chart, and recent-activity data so the widget stays thin
and later caching/optimization can be implemented in one place.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, date
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
            'summary': self._safe_call(self.summary, {}),
            'monthly_trend': self._safe_call(self.monthly_trend, []),
            'recent_entries': self._safe_call(lambda: self.recent_entries(limit=5), []),
            'cashbox_movement': self._safe_call(self.cashbox_movement, {}),
        }
        self._cache = data
        self._cache_time = datetime.now()
        return data

    def _safe_call(self, func, default):
        try:
            return func()
        except Exception as exc:
            print(f"⚠️ تعذر تحميل بيانات لوحة التحكم: {exc}")
            return default

    def summary(self) -> Dict:
        try:
            summary = reporting_service.summary()
        except Exception as exc:
            print(f"⚠️ تعذر تحميل ملخص التقارير للوحة التحكم: {exc}")
            summary = {}
        if not isinstance(summary, dict):
            summary = {}
        keys = ('cash_balance', 'total_sales', 'total_purchases', 'total_expenses',
                'receivables', 'payables', 'net_profit', 'total_incoming',
                'total_outgoing', 'cash_received', 'cash_paid', 'cash_net_movement')
        return {k: self._decimal(summary.get(k, 0)) for k in keys}

    def cashbox_movement(self) -> Dict:
        """Return today and all-time cash movement summaries.

        Amounts are kept in the system base currency. The dashboard converts
        them to the selected display currency, keeping exchange-rate edits in
        settings only.
        """
        today = date.today().isoformat()
        today_summary = self._normalize_cash_movement(reporting_service.summary(today, today))
        total_summary = self._normalize_cash_movement(reporting_service.summary())
        return {'today': today_summary, 'general': total_summary}

    def _normalize_cash_movement(self, summary: Dict) -> Dict:
        if not isinstance(summary, dict):
            summary = {}
        received = self._decimal(summary.get('cash_received', summary.get('total_incoming', summary.get('total_sales', 0))))
        paid = self._decimal(summary.get('cash_paid', summary.get('total_outgoing', 0)))
        net = self._decimal(summary.get('cash_net_movement', received - paid))
        return {'received': received, 'paid': paid, 'net': net}

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
