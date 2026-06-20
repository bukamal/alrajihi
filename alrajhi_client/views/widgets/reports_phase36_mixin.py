# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from i18n import translate as tr
from core.services.reporting_service import reporting_service
from currency import currency


class ReportsPhase36Mixin:
    def _refresh_phase36_reports(self, start, end, display_curr):
        """Refresh Phase 36 extended reports.

        This method is intentionally defensive: one optional diagnostic report
        should not prevent the Reports page from opening.  Critical business
        reports are still populated when their service/API is available, while
        unavailable diagnostics show an empty table instead of raising.
        """
        customer_id = self.customer_filter.currentData() if hasattr(self, 'customer_filter') else None
        supplier_id = self.supplier_filter.currentData() if hasattr(self, 'supplier_filter') else None
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        item_id = self.item_filter.currentData() if hasattr(self, 'item_filter') else None

        if self.tabs.currentWidget() in (self.general_ledger_tab, self.full_trial_balance_tab, self.slow_items_tab, self.top_items_tab, self.low_items_tab, self.reorder_items_tab, self.report_audit_tab):
            self._refresh_phase141_reports(start, end, display_curr)
            return

        # Trial balance
        try:
            rows = []
            for r in reporting_service.trial_balance():
                debit = Decimal(str(r.get('debit') or r.get('debit_total') or 0))
                credit = Decimal(str(r.get('credit') or r.get('credit_total') or 0))
                rows.append({
                    'account': r.get('account_name') or r.get('name') or r.get('account') or '',
                    'code': r.get('code') or r.get('account_code') or '',
                    'debit': currency.format_amount(currency.convert(debit, currency.storage_currency(), display_curr)),
                    'credit': currency.format_amount(currency.convert(credit, currency.storage_currency(), display_curr)),
                    'balance': currency.format_amount(currency.convert(debit - credit, currency.storage_currency(), display_curr)),
                })
            self._set_table(self.trial_balance_table, rows, ['الحساب', 'الكود', 'مدين', 'دائن', 'الرصيد'], ['account', 'code', 'debit', 'credit', 'balance'])
        except Exception:
            self._set_table(self.trial_balance_table, [], ['الحساب', 'الكود', 'مدين', 'دائن', 'الرصيد'], ['account', 'code', 'debit', 'credit', 'balance'])

        # Customer statement
        try:
            rows = []
            if customer_id:
                for r in reporting_service.customer_statement(customer_id, start, end):
                    debit = Decimal(str(r.get('debit') or 0))
                    credit = Decimal(str(r.get('credit') or 0))
                    balance = Decimal(str(r.get('balance') if r.get('balance') is not None else debit - credit))
                    debit_display = currency.convert(debit, currency.storage_currency(), display_curr)
                    credit_display = currency.convert(credit, currency.storage_currency(), display_curr)
                    balance_display = currency.convert(balance, currency.storage_currency(), display_curr)
                    rows.append({
                        'date': r.get('date') or r.get('created_at') or r.get('invoice_date') or '',
                        'type': self._report_source_label(r.get('source_type') or r.get('type') or r.get('source') or r.get('movement_type')),
                        'ref': r.get('reference') or r.get('reference_no') or r.get('invoice_no') or r.get('voucher_no') or '',
                        'desc': self._report_source_label(r.get('description') or r.get('source_type')),
                        'debit': currency.format_amount(debit_display),
                        'credit': currency.format_amount(credit_display),
                        'balance': currency.format_amount(balance_display),
                        'debit_raw': debit_display,
                        'credit_raw': credit_display,
                        'balance_raw': balance_display,
                    })
            self._set_table(self.customer_statement_table, rows, [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.customer_statement_tab:
                self._set_summary(self._statement_summary(rows) if rows else tr('choose_customer'))
        except Exception as exc:
            self._set_table(self.customer_statement_table, [], [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.customer_statement_tab:
                self._set_summary(tr('reports_refresh_failed', error=str(exc)))

        # Supplier statement
        try:
            rows = []
            if supplier_id:
                for r in reporting_service.supplier_statement(supplier_id, start, end):
                    debit = Decimal(str(r.get('debit') or 0))
                    credit = Decimal(str(r.get('credit') or 0))
                    balance = Decimal(str(r.get('balance') if r.get('balance') is not None else credit - debit))
                    debit_display = currency.convert(debit, currency.storage_currency(), display_curr)
                    credit_display = currency.convert(credit, currency.storage_currency(), display_curr)
                    balance_display = currency.convert(balance, currency.storage_currency(), display_curr)
                    rows.append({
                        'date': r.get('date') or r.get('created_at') or r.get('invoice_date') or '',
                        'type': self._report_source_label(r.get('source_type') or r.get('type') or r.get('source') or r.get('movement_type')),
                        'ref': r.get('reference') or r.get('reference_no') or r.get('invoice_no') or r.get('voucher_no') or '',
                        'desc': self._report_source_label(r.get('description') or r.get('source_type')),
                        'debit': currency.format_amount(debit_display),
                        'credit': currency.format_amount(credit_display),
                        'balance': currency.format_amount(balance_display),
                        'debit_raw': debit_display,
                        'credit_raw': credit_display,
                        'balance_raw': balance_display,
                    })
            self._set_table(self.supplier_statement_table, rows, [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.supplier_statement_tab:
                self._set_summary(self._statement_summary(rows) if rows else tr('choose_supplier'))
        except Exception as exc:
            self._set_table(self.supplier_statement_table, [], [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.supplier_statement_tab:
                self._set_summary(tr('reports_refresh_failed', error=str(exc)))

        # Customer/Supplier balances
        try:
            rows = []
            for r in reporting_service.customer_balances():
                bal = Decimal(str(r.get('balance') or r.get('current_balance') or 0))
                rows.append({'name': r.get('name') or r.get('customer_name') or '', 'phone': r.get('phone') or '', 'balance': currency.format_amount(currency.convert(bal, currency.storage_currency(), display_curr))})
            self._set_table(self.customer_balances_table, rows, ['العميل', 'الهاتف', 'الرصيد'], ['name','phone','balance'])
        except Exception:
            self._set_table(self.customer_balances_table, [], ['العميل', 'الهاتف', 'الرصيد'], ['name','phone','balance'])
        try:
            rows = []
            for r in reporting_service.supplier_balances():
                bal = Decimal(str(r.get('balance') or r.get('current_balance') or 0))
                rows.append({'name': r.get('name') or r.get('supplier_name') or '', 'phone': r.get('phone') or '', 'balance': currency.format_amount(currency.convert(bal, currency.storage_currency(), display_curr))})
            self._set_table(self.supplier_balances_table, rows, ['المورد', 'الهاتف', 'الرصيد'], ['name','phone','balance'])
        except Exception:
            self._set_table(self.supplier_balances_table, [], ['المورد', 'الهاتف', 'الرصيد'], ['name','phone','balance'])

        # Aging
        try:
            rows = []
            for r in reporting_service.customer_aging(end):
                rows.append({
                    'name': r.get('name') or r.get('customer_name') or '',
                    'current': currency.format_amount(currency.convert(Decimal(str(r.get('current') or r.get('not_due') or 0)), currency.storage_currency(), display_curr)),
                    'd30': currency.format_amount(currency.convert(Decimal(str(r.get('days_1_30') or r.get('d30') or 0)), currency.storage_currency(), display_curr)),
                    'd60': currency.format_amount(currency.convert(Decimal(str(r.get('days_31_60') or r.get('d60') or 0)), currency.storage_currency(), display_curr)),
                    'd90': currency.format_amount(currency.convert(Decimal(str(r.get('days_61_90') or r.get('d90') or 0)), currency.storage_currency(), display_curr)),
                    'over': currency.format_amount(currency.convert(Decimal(str(r.get('over_90') or r.get('older') or 0)), currency.storage_currency(), display_curr)),
                    'total': currency.format_amount(currency.convert(Decimal(str(r.get('total') or r.get('balance') or 0)), currency.storage_currency(), display_curr)),
                })
            self._set_table(self.customer_aging_table, rows, ['العميل', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])
        except Exception:
            self._set_table(self.customer_aging_table, [], ['العميل', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])
        try:
            rows = []
            for r in reporting_service.supplier_aging(end):
                rows.append({
                    'name': r.get('name') or r.get('supplier_name') or '',
                    'current': currency.format_amount(currency.convert(Decimal(str(r.get('current') or r.get('not_due') or 0)), currency.storage_currency(), display_curr)),
                    'd30': currency.format_amount(currency.convert(Decimal(str(r.get('days_1_30') or r.get('d30') or 0)), currency.storage_currency(), display_curr)),
                    'd60': currency.format_amount(currency.convert(Decimal(str(r.get('days_31_60') or r.get('d60') or 0)), currency.storage_currency(), display_curr)),
                    'd90': currency.format_amount(currency.convert(Decimal(str(r.get('days_61_90') or r.get('d90') or 0)), currency.storage_currency(), display_curr)),
                    'over': currency.format_amount(currency.convert(Decimal(str(r.get('over_90') or r.get('older') or 0)), currency.storage_currency(), display_curr)),
                    'total': currency.format_amount(currency.convert(Decimal(str(r.get('total') or r.get('balance') or 0)), currency.storage_currency(), display_curr)),
                })
            self._set_table(self.supplier_aging_table, rows, ['المورد', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])
        except Exception:
            self._set_table(self.supplier_aging_table, [], ['المورد', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])

        # Ledger diagnostics
        try:
            from core.services.inventory_service import inventory_service
            rec = inventory_service.ledger_reconciliation(warehouse_id=wh_id, tolerance='0')
            rec_rows = self._rows_from(rec, 'mismatches', 'rows')
            if not rec_rows and isinstance(rec, dict):
                rec_rows = rec.get('item_differences') or rec.get('warehouse_differences') or []
            rows = []
            for r in rec_rows:
                diff = Decimal(str(r.get('difference') or r.get('delta') or 0))
                rows.append({
                    'scope': r.get('scope') or r.get('level') or '',
                    'item': r.get('item_name') or r.get('item_id') or '',
                    'warehouse': r.get('warehouse_name') or r.get('warehouse_id') or '',
                    'operational': r.get('operational_balance') or r.get('operational_qty') or r.get('quantity') or '0',
                    'ledger': r.get('ledger_balance') or r.get('ledger_qty') or '0',
                    'difference': str(diff),
                })
            self._set_table(self.ledger_reconciliation_table, rows, ['النطاق', 'المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق'], ['scope','item','warehouse','operational','ledger','difference'])

            dual = inventory_service.ledger_dual_read(warehouse_id=wh_id, tolerance='0', include_matches=False)
            dual_rows = self._rows_from(dual, 'rows', 'differences', 'mismatches')
            rows = []
            for r in dual_rows:
                rows.append({
                    'item': r.get('item_name') or r.get('item_id') or '',
                    'warehouse': r.get('warehouse_name') or r.get('warehouse_id') or '',
                    'operational': r.get('operational_balance') or r.get('operational_qty') or '0',
                    'ledger': r.get('ledger_balance') or r.get('ledger_qty') or '0',
                    'difference': r.get('difference') or r.get('delta') or '0',
                    'status': r.get('status') or ('مطابق' if str(r.get('difference') or '0') == '0' else 'فرق'),
                })
            self._set_table(self.ledger_dual_read_table, rows, ['المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق', 'الحالة'], ['item','warehouse','operational','ledger','difference','status'])

            ready = inventory_service.ledger_readiness(warehouse_id=wh_id, tolerance='0')
            rows = []
            for key in ('blockers', 'warnings'):
                for value in ready.get(key, []) if isinstance(ready, dict) else []:
                    rows.append({'type': 'مانع' if key == 'blockers' else 'تحذير', 'message': str(value)})
            if isinstance(ready, dict):
                rows.insert(0, {'type': 'القرار', 'message': ready.get('recommendation') or ('جاهز للقراءة المزدوجة' if ready.get('safe_for_dual_read') else 'غير جاهز')})
            self._set_table(self.ledger_readiness_table, rows, ['النوع', 'الرسالة'], ['type','message'])
        except Exception:
            self._set_table(self.ledger_reconciliation_table, [], ['النطاق', 'المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق'], ['scope','item','warehouse','operational','ledger','difference'])
            self._set_table(self.ledger_dual_read_table, [], ['المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق', 'الحالة'], ['item','warehouse','operational','ledger','difference','status'])
            self._set_table(self.ledger_readiness_table, [], ['النوع', 'الرسالة'], ['type','message'])


        # Item movement report
        try:
            rows = []
            total_in = Decimal('0')
            total_out = Decimal('0')
            for r in reporting_service.item_movement_report(item_id=item_id, warehouse_id=wh_id, start_date=start, end_date=end):
                in_qty = Decimal(str(r.get('in_qty') or 0))
                out_qty = Decimal(str(r.get('out_qty') or 0))
                total_in += in_qty
                total_out += out_qty
                rows.append({
                    'date': r.get('movement_date') or '',
                    'reference': f"{r.get('reference_type') or ''} #{r.get('reference_id') or ''}".strip(),
                    'item': r.get('item_name') or r.get('item_id') or '',
                    'barcode': r.get('barcode') or '',
                    'warehouse': r.get('warehouse_name') or '',
                    'movement': self._movement_label(r.get('movement_type')),
                    'in_qty': f"{in_qty:.4f}".rstrip('0').rstrip('.'),
                    'out_qty': f"{out_qty:.4f}".rstrip('0').rstrip('.'),
                    'balance': f"{Decimal(str(r.get('balance_qty') or 0)):.4f}".rstrip('0').rstrip('.'),
                    'unit_cost': currency.format_amount(currency.convert(Decimal(str(r.get('unit_cost') or 0)), currency.storage_currency(), display_curr)),
                    'total_cost': currency.format_amount(currency.convert(Decimal(str(r.get('total_cost') or 0)), currency.storage_currency(), display_curr)),
                    'notes': r.get('notes') or '',
                })
            self._set_table(
                self.item_movement_table,
                rows,
                [tr('date'), tr('reference'), tr('print_item'), tr('barcode'), tr('warehouse_label'), tr('movement_type'), tr('in_qty'), tr('out_qty'), tr('balance'), tr('unit_cost'), tr('total_cost'), tr('notes')],
                ['date', 'reference', 'item', 'barcode', 'warehouse', 'movement', 'in_qty', 'out_qty', 'balance', 'unit_cost', 'total_cost', 'notes']
            )
            if self.tabs.currentWidget() is self.item_movement_tab:
                self._set_summary(f"{tr('rows_count')}: {len(rows)} | {tr('in_qty')}: {total_in} | {tr('out_qty')}: {total_out}")
        except Exception:
            self._set_table(self.item_movement_table, [], [tr('date'), tr('reference'), tr('print_item'), tr('barcode'), tr('warehouse_label'), tr('movement_type'), tr('in_qty'), tr('out_qty'), tr('balance'), tr('unit_cost'), tr('total_cost'), tr('notes')], ['date','reference','item','barcode','warehouse','movement','in_qty','out_qty','balance','unit_cost','total_cost','notes'])

        # Invoice profitability report
        try:
            rows = []
            total_sales = Decimal('0')
            total_cost = Decimal('0')
            total_profit = Decimal('0')
            for r in reporting_service.invoice_profit_report(start_date=start, end_date=end, customer_id=customer_id):
                invoice_total = Decimal(str(r.get('invoice_total') or 0))
                cost_total = Decimal(str(r.get('cost_total') or 0))
                profit = Decimal(str(r.get('profit') or 0))
                total_sales += invoice_total
                total_cost += cost_total
                total_profit += profit
                rows.append({
                    'date': r.get('date') or '',
                    'reference': r.get('reference') or r.get('id') or '',
                    'customer': r.get('customer_name') or '',
                    'sales': currency.format_amount(currency.convert(invoice_total, currency.storage_currency(), display_curr)),
                    'cost': currency.format_amount(currency.convert(cost_total, currency.storage_currency(), display_curr)),
                    'profit': currency.format_amount(currency.convert(profit, currency.storage_currency(), display_curr)),
                    'margin': f"{Decimal(str(r.get('profit_margin') or 0)):.2f}%",
                })
            self._set_table(
                self.invoice_profit_table,
                rows,
                [tr('date'), tr('reference'), tr('customer_label'), tr('sales_value'), tr('cost'), tr('profit'), tr('profit_margin')],
                ['date', 'reference', 'customer', 'sales', 'cost', 'profit', 'margin']
            )
            if self.tabs.currentWidget() is self.invoice_profit_tab:
                self._set_summary(f"{tr('rows_count')}: {len(rows)} | {tr('sales_value')}: {currency.format_amount(currency.convert(total_sales, currency.storage_currency(), display_curr))} | {tr('cost')}: {currency.format_amount(currency.convert(total_cost, currency.storage_currency(), display_curr))} | {tr('profit')}: {currency.format_amount(currency.convert(total_profit, currency.storage_currency(), display_curr))}")
        except Exception:
            self._set_table(self.invoice_profit_table, [], [tr('date'), tr('reference'), tr('customer_label'), tr('sales_value'), tr('cost'), tr('profit'), tr('profit_margin')], ['date','reference','customer','sales','cost','profit','margin'])

        # Offline queue diagnostics
        try:
            from core.services.offline_queue_service import offline_queue_service
            rows = []
            for r in offline_queue_service.recent(limit=300):
                rows.append({
                    'id': r.get('id'),
                    'method': r.get('method') or '',
                    'endpoint': r.get('endpoint') or '',
                    'status': r.get('status') or '',
                    'attempts': r.get('attempts') or 0,
                    'error': r.get('last_error') or r.get('error') or '',
                    'created': r.get('created_at') or '',
                })
            self._set_table(self.offline_queue_table, rows, ['#', 'الطريقة', 'المسار', 'الحالة', 'المحاولات', 'الخطأ', 'التاريخ'], ['id','method','endpoint','status','attempts','error','created'])
        except Exception:
            self._set_table(self.offline_queue_table, [], ['#', 'الطريقة', 'المسار', 'الحالة', 'المحاولات', 'الخطأ', 'التاريخ'], ['id','method','endpoint','status','attempts','error','created'])

        # Unit conversion audit
        try:
            from core.services.product_service import product_service
            rows = []
            for item in product_service.items(limit=1000):
                units = product_service.item_units(item.get('id')) if item.get('id') else []
                base_unit = item.get('unit') or item.get('base_unit') or ''
                if not units:
                    rows.append({'item': item.get('name') or '', 'base': base_unit, 'unit': '—', 'factor': '1', 'status': 'لا توجد وحدات فرعية'})
                    continue
                seen = set()
                for u in units:
                    name = u.get('unit_name') or u.get('name') or ''
                    factor = Decimal(str(u.get('conversion_factor') or 0))
                    status = 'سليم'
                    if not name:
                        status = 'اسم وحدة فارغ'
                    elif name in seen:
                        status = 'وحدة مكررة'
                    elif factor <= 0:
                        status = 'معامل غير صالح'
                    seen.add(name)
                    rows.append({'item': item.get('name') or '', 'base': base_unit, 'unit': name, 'factor': str(factor), 'status': status})
            self._set_table(self.unit_audit_table, rows, [tr('print_item'), tr('base_unit'), tr('print_unit'), tr('conversion_factor'), tr('status')], ['item','base','unit','factor','status'])
        except Exception:
            self._set_table(self.unit_audit_table, [], [tr('print_item'), tr('base_unit'), tr('print_unit'), tr('conversion_factor'), tr('status')], ['item','base','unit','factor','status'])


    def _refresh_phase141_reports(self, start, end, display_curr):
        tab = self.tabs.currentWidget()
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        # General ledger
        if tab is self.general_ledger_tab:
            rows=[]
            for r in reporting_service.general_ledger_report(start_date=start, end_date=end):
                rows.append({
                    'date': r.get('entry_date') or '',
                    'account': f"{r.get('account_code') or ''} {r.get('account_name') or ''}".strip(),
                    'reference': r.get('reference') or r.get('entry_id') or '',
                    'description': r.get('description') or '',
                    'debit': currency.format_amount(currency.convert(Decimal(str(r.get('debit') or 0)), currency.storage_currency(), display_curr)),
                    'credit': currency.format_amount(currency.convert(Decimal(str(r.get('credit') or 0)), currency.storage_currency(), display_curr)),
                    'balance': currency.format_amount(currency.convert(Decimal(str(r.get('balance') or 0)), currency.storage_currency(), display_curr)),
                })
            self._set_table(self.general_ledger_table, rows, [tr('date'), tr('account'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','account','reference','description','debit','credit','balance'])
            self._set_summary(f"{tr('rows_count')}: {len(rows)}")
            return
        # Full trial balance
        if tab is self.full_trial_balance_tab:
            tb = reporting_service.full_trial_balance_report(start, end)
            rows=[]
            for r in tb.get('rows') or []:
                rows.append({
                    'code': r.get('code') or r.get('account_code') or '',
                    'account': r.get('account_name') or r.get('name') or r.get('account') or '',
                    'debit': currency.format_amount(currency.convert(Decimal(str(r.get('debit') or 0)), currency.storage_currency(), display_curr)),
                    'credit': currency.format_amount(currency.convert(Decimal(str(r.get('credit') or 0)), currency.storage_currency(), display_curr)),
                    'balance': currency.format_amount(currency.convert(Decimal(str(r.get('balance') or 0)), currency.storage_currency(), display_curr)),
                })
            self._set_table(self.full_trial_balance_table, rows, [tr('code'), tr('account'), tr('debit'), tr('credit'), tr('balance')], ['code','account','debit','credit','balance'])
            self._set_summary(f"{tr('debit')}: {currency.format_amount(currency.convert(Decimal(str(tb.get('total_debit') or 0)), currency.storage_currency(), display_curr))} | {tr('credit')}: {currency.format_amount(currency.convert(Decimal(str(tb.get('total_credit') or 0)), currency.storage_currency(), display_curr))} | {tr('difference')}: {currency.format_amount(currency.convert(Decimal(str(tb.get('difference') or 0)), currency.storage_currency(), display_curr))}")
            return
        # Smart item reports
        smart_map = {
            self.slow_items_tab: ('slow', self.slow_items_table),
            self.top_items_tab: ('top', self.top_items_table),
            self.low_items_tab: ('low', self.low_items_table),
            self.reorder_items_tab: ('reorder', self.reorder_items_table),
        }
        if tab in smart_map:
            kind, table = smart_map[tab]
            rows=[]
            for r in reporting_service.smart_items_report(kind, start_date=start, end_date=end, warehouse_id=wh_id):
                rows.append({
                    'item': r.get('name') or r.get('item_name') or '',
                    'barcode': r.get('barcode') or '',
                    'warehouse': r.get('warehouse_name') or '',
                    'qty': str(r.get('qty') if r.get('qty') is not None else r.get('quantity') or 0),
                    'min_stock': str(r.get('min_stock') or ''),
                    'shortage': str(r.get('shortage') or ''),
                    'last_sale': r.get('last_sale_date') or '',
                    'days': str(r.get('days_without_movement') if r.get('days_without_movement') is not None else ''),
                    'sales': currency.format_amount(currency.convert(Decimal(str(r.get('sales_value') or 0)), currency.storage_currency(), display_curr)),
                    'profit': currency.format_amount(currency.convert(Decimal(str(r.get('profit') or 0)), currency.storage_currency(), display_curr)),
                })
            if kind == 'reorder':
                headers=[tr('print_item'), tr('barcode'), tr('warehouse_label'), tr('quantity'), tr('min_stock'), tr('shortage')]
                keys=['item','barcode','warehouse','qty','min_stock','shortage']
            elif kind == 'slow':
                headers=[tr('print_item'), tr('barcode'), tr('last_sale'), tr('days_without_movement'), tr('quantity')]
                keys=['item','barcode','last_sale','days','qty']
            else:
                headers=[tr('print_item'), tr('barcode'), tr('quantity'), tr('sales_value'), tr('profit')]
                keys=['item','barcode','qty','sales','profit']
            self._set_table(table, rows, headers, keys)
            self._set_summary(f"{tr('rows_count')}: {len(rows)}")
            return
        # Consistency audit
        if tab is self.report_audit_tab:
            rows=[]
            for r in reporting_service.report_consistency_audit(start, end):
                rows.append({'scope': r.get('scope') or '', 'status': r.get('status') or '', 'severity': r.get('severity') or '', 'message': r.get('message') or ''})
            self._set_table(self.report_audit_table, rows, [tr('scope'), tr('status'), tr('severity'), tr('message')], ['scope','status','severity','message'])
            self._set_summary(f"{tr('rows_count')}: {len(rows)}")
            return

    def print_report(self, mode='preview'):
        try:
            self._require_report_print_permission(context=f'report_print:{mode}')
        except AttributeError:
            from core.services.report_operation_policy import report_operation_policy
            report_operation_policy.require(report_operation_policy.OP_PRINT, context=f'report_print:{mode}')
        from printing.printing_service import printing_service
        start, end = self.get_date_range()
        tab = self.tabs.currentWidget()
        title = self.tabs.tabText(self.tabs.currentIndex())
        table = None
        if tab is self.income_tab:
            table = self.income_table
        elif tab is self.balance_tab:
            table = self.balance_table
        elif tab is self.wh_valuation_tab:
            table = self.wh_valuation_table
        elif tab is self.wh_balances_tab:
            table = self.wh_balances_table
        elif tab is self.wh_movements_tab:
            table = self.wh_movements_table
        elif tab is self.wh_transfers_tab:
            table = self.wh_transfers_table
        elif tab is self.cash_summary_tab:
            table = self.cash_summary_table
        elif tab is self.cash_movements_tab:
            table = self.cash_movements_table
        elif tab is self.bank_movements_tab:
            table = self.bank_movements_table
        elif tab is self.pos_shifts_tab:
            table = self.pos_shifts_table
        elif tab is self.trial_balance_tab:
            table = self.trial_balance_table
        elif tab is self.customer_statement_tab:
            table = self.customer_statement_table
        elif tab is self.supplier_statement_tab:
            table = self.supplier_statement_table
        elif tab is self.customer_balances_tab:
            table = self.customer_balances_table
        elif tab is self.supplier_balances_tab:
            table = self.supplier_balances_table
        elif tab is self.customer_aging_tab:
            table = self.customer_aging_table
        elif tab is self.supplier_aging_tab:
            table = self.supplier_aging_table
        elif tab is self.ledger_reconciliation_tab:
            table = self.ledger_reconciliation_table
        elif tab is self.ledger_dual_read_tab:
            table = self.ledger_dual_read_table
        elif tab is self.ledger_readiness_tab:
            table = self.ledger_readiness_table
        elif tab is self.offline_queue_tab:
            table = self.offline_queue_table
        elif tab is self.unit_audit_tab:
            table = self.unit_audit_table
        elif tab is self.item_movement_tab:
            table = self.item_movement_table
        elif tab is self.invoice_profit_tab:
            table = self.invoice_profit_table
        elif tab is self.net_profit_tab:
            table = self.net_profit_table
        elif tab is self.manufacturing_orders_tab:
            table = self.manufacturing_orders_table
        elif tab is self.product_cost_tab:
            table = self.product_cost_table
        elif tab is self.general_ledger_tab:
            table = self.general_ledger_table
        elif tab is self.full_trial_balance_tab:
            table = self.full_trial_balance_table
        elif tab is self.slow_items_tab:
            table = self.slow_items_table
        elif tab is self.top_items_tab:
            table = self.top_items_table
        elif tab is self.low_items_tab:
            table = self.low_items_table
        elif tab is self.reorder_items_tab:
            table = self.reorder_items_table
        elif tab is self.report_audit_tab:
            table = self.report_audit_table
        if not table or not table.model():
            return
        model = table.model()
        headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(model.columnCount())]
        rows = []
        for r in range(model.rowCount()):
            rows.append([model.data(model.index(r, c), Qt.DisplayRole) or '' for c in range(model.columnCount())])
        subtitle = tr('period_subtitle', start=start, end=end)
        summary = {}
        try:
            descriptor = self._current_report_descriptor()
            if descriptor is not None:
                summary = {
                    tr('report_shell_report_key'): descriptor.report_key,
                    tr('report_shell_api_resource'): descriptor.api_resource,
                    tr('report_shell_network_mode'): descriptor.network_mode,
                    tr('report_shell_currency'): getattr(descriptor, 'currency_policy', ''),
                }
        except Exception:
            summary = {}
        # Phase 236/256: visible report print buttons always use Browser HTML and Report Shell metadata.
        printing_service.report_print(title, rows, headers, self, subtitle=subtitle, summary=summary)
