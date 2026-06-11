# -*- coding: utf-8 -*-
"""Operational dashboard alerts.

Alerts are read-only summaries for the UI.  They intentionally avoid changing
business state; they only describe issues users should inspect.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List
import datetime
import os
from PyQt5.QtCore import QSettings

from core.services.product_service import product_service
from core.services.invoice_service import invoice_service
from core.services.settings_service import settings_service
from core.services.cashbox_service import cashbox_service


class AlertService:
    def dashboard_alerts(self, limit: int = 10) -> List[Dict]:
        alerts: List[Dict] = []
        alerts.extend(self.system_alerts())
        remaining = max(0, limit - len(alerts))
        if remaining:
            alerts.extend(self.inventory_alerts(limit=remaining))
        remaining = max(0, limit - len(alerts))
        if remaining:
            alerts.extend(self.unpaid_invoice_alerts(limit=remaining))
        return alerts[:limit]

    def system_alerts(self) -> List[Dict]:
        alerts: List[Dict] = []
        alerts.extend(self.backup_alerts())
        alerts.extend(self.shift_alerts())
        return alerts

    def backup_alerts(self) -> List[Dict]:
        try:
            settings = QSettings('AlRajhi', 'Settings')
            enabled = settings.value('backup/enabled', False, type=bool)
            folder = str(settings.value('backup/folder', '') or '').strip()
            if not enabled:
                return [{
                    'severity': 'info',
                    'type': 'BACKUP',
                    'title': 'النسخ الاحتياطي غير مفعل',
                    'message': 'يفضل تفعيل النسخ الاحتياطي التلقائي من الإعدادات',
                    'target': 'settings',
                    'entity_id': None,
                }]
            if not folder or not os.path.isdir(folder):
                return [{
                    'severity': 'warning',
                    'type': 'BACKUP',
                    'title': 'مجلد النسخ الاحتياطي غير صالح',
                    'message': 'اختر مجلد نسخ احتياطي صحيح من الإعدادات',
                    'target': 'settings',
                    'entity_id': None,
                }]
            today = datetime.date.today().strftime('%Y%m%d')
            has_today_backup = any(name.startswith('alrajhi_backup_' + today) and name.endswith('.db') for name in os.listdir(folder))
            if not has_today_backup:
                return [{
                    'severity': 'warning',
                    'type': 'BACKUP',
                    'title': 'لا توجد نسخة احتياطية اليوم',
                    'message': 'لم يتم العثور على نسخة احتياطية بتاريخ اليوم في المجلد المحدد',
                    'target': 'settings',
                    'entity_id': None,
                }]
        except Exception:
            return []
        return []

    def shift_alerts(self) -> List[Dict]:
        try:
            if not cashbox_service.pos_shifts_enabled():
                return []
            shift = cashbox_service.current_open_shift()
            if not shift:
                return []
            opened_at = str(shift.get('opened_at') or '')[:16].replace('T', ' ')
            return [{
                'severity': 'info',
                'type': 'POS_SHIFT',
                'title': 'وردية مفتوحة',
                'message': f"{shift.get('cashbox_name', 'الصندوق')} — منذ {opened_at}",
                'target': 'cashboxes',
                'entity_id': shift.get('id'),
            }]
        except Exception:
            return []

    def inventory_alerts(self, limit: int = 10) -> List[Dict]:
        default_threshold = self._threshold()
        alerts = []
        for item in product_service.items(limit=1000):
            qty = self._decimal(item.get('available', item.get('quantity', 0)))
            item_threshold = self._decimal(item.get('reorder_level', 0))
            threshold = item_threshold if item_threshold > 0 else default_threshold
            if qty <= 0:
                severity = 'critical'
                title = 'نفاد مخزون'
            elif threshold > 0 and qty <= threshold:
                severity = 'warning'
                title = 'مخزون منخفض'
            else:
                continue
            alerts.append({
                'severity': severity,
                'type': 'INVENTORY',
                'title': title,
                'message': f"{item.get('name', '')} — الكمية الحالية: {qty} / حد إعادة الطلب: {threshold}",
                'target': 'items',
                'entity_id': item.get('id'),
            })
            if len(alerts) >= limit:
                break
        return alerts

    def unpaid_invoice_alerts(self, limit: int = 10) -> List[Dict]:
        alerts = []
        for inv in invoice_service.unpaid_invoices(inv_type=None, limit=200):
            try:
                remaining = self._decimal(inv.get('total', 0)) - self._decimal(inv.get('paid', 0))
            except Exception:
                remaining = Decimal('0')
            if remaining <= 0:
                continue
            inv_type = inv.get('type')
            title = 'فاتورة بيع غير مدفوعة' if inv_type == 'sale' else 'فاتورة شراء غير مدفوعة'
            alerts.append({
                'severity': 'info',
                'type': 'INVOICE',
                'title': title,
                'message': f"{inv.get('reference', inv.get('id', ''))} — المتبقي: {remaining}",
                'target': 'invoices',
                'entity_id': inv.get('id'),
            })
            if len(alerts) >= limit:
                break
        return alerts

    def _threshold(self) -> Decimal:
        value = settings_service.get('low_stock_threshold', '5')
        return self._decimal(value) if self._decimal(value) > 0 else Decimal('5')

    def _decimal(self, value) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except Exception:
            return Decimal('0')


alert_service = AlertService()
