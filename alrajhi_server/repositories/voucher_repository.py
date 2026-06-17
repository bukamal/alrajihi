from __future__ import annotations

from decimal import Decimal
from typing import Any

from alrajhi_server.database.connection import get_db


def _dec(value: Any, default: str = '0') -> Decimal:
    try:
        return Decimal(str(value if value is not None else default))
    except Exception:
        return Decimal(default)


class VoucherRepository:
    """Voucher persistence and accounting side-effects boundary."""

    def __init__(self) -> None:
        self._db = get_db()

    def list_vouchers(self, user_id: Any, vtype: str | None = None, limit: int | None = None, offset: int | None = None) -> dict[str, Any]:
        query = """
            SELECT v.*, b.name AS branch_name, c.name AS cashbox_name, ba.bank_name AS bank_name, ba.account_name AS bank_account_name
            FROM vouchers v
            LEFT JOIN branches b ON b.id=v.branch_id
            LEFT JOIN cashboxes c ON c.id=v.cashbox_id
            LEFT JOIN bank_accounts ba ON ba.id=v.bank_account_id
            WHERE v.user_id = ?
        """
        count_query = "SELECT COUNT(*) FROM vouchers WHERE user_id = ?"
        params: list[Any] = [user_id]
        count_params: list[Any] = [user_id]
        if vtype in ('receipt', 'payment', 'expense'):
            query += " AND v.type = ?"
            count_query += " AND type = ?"
            params.append(vtype)
            count_params.append(vtype)
        total = self._db.execute(count_query, count_params).fetchone()[0]
        query += " ORDER BY v.id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = self._db.execute(query, params).fetchall()
        return {'vouchers': [dict(row) for row in rows], 'total': total}

    def get_voucher(self, user_id: Any, voucher_id: int) -> dict[str, Any] | None:
        row = self._db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
        return dict(row) if row else None

    def validate_payload(self, user_id: Any, data: dict[str, Any], exclude_voucher_id: int | None = None) -> None:
        vtype = data.get('type')
        if vtype not in ('receipt', 'payment', 'expense'):
            raise ValueError('نوع السند غير صالح')
        amount = _dec(data.get('amount'))
        if amount <= 0:
            raise ValueError('مبلغ السند يجب أن يكون أكبر من صفر')
        customer_id = data.get('customer_id')
        supplier_id = data.get('supplier_id')
        invoice_id = data.get('invoice_id')
        if vtype == 'receipt':
            if not customer_id or supplier_id:
                raise ValueError('سند القبض يجب أن يرتبط بعميل فقط')
        elif vtype == 'payment':
            if not supplier_id or customer_id:
                raise ValueError('سند الدفع يجب أن يرتبط بمورد فقط')
        elif vtype == 'expense':
            if invoice_id:
                raise ValueError('سند المصروف لا يجب ربطه بفاتورة')
            if customer_id or supplier_id:
                raise ValueError('سند المصروف لا يجب ربطه بعميل أو مورد')
        if not invoice_id:
            return
        inv = self._db.execute("SELECT * FROM invoices WHERE id=? AND user_id=? AND deleted_at IS NULL", (invoice_id, user_id)).fetchone()
        if not inv:
            raise ValueError('الفاتورة المرتبطة غير موجودة أو محذوفة')
        if vtype == 'receipt' and inv['type'] != 'sale':
            raise ValueError('سند القبض لا يرتبط إلا بفاتورة بيع')
        if vtype == 'payment' and inv['type'] != 'purchase':
            raise ValueError('سند الدفع لا يرتبط إلا بفاتورة شراء')
        if vtype == 'receipt' and customer_id and inv['customer_id'] != customer_id:
            raise ValueError('العميل في السند لا يطابق عميل الفاتورة')
        if vtype == 'payment' and supplier_id and inv['supplier_id'] != supplier_id:
            raise ValueError('المورد في السند لا يطابق مورد الفاتورة')
        old_amount = Decimal('0')
        if exclude_voucher_id is not None:
            old = self._db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (exclude_voucher_id, user_id)).fetchone()
            if old and old['invoice_id'] == invoice_id:
                old_amount = _dec(old['amount'])
        remaining = _dec(inv['total']) - (_dec(inv['paid']) - old_amount)
        if amount > remaining:
            raise ValueError(f'مبلغ السند يتجاوز المتبقي على الفاتورة ({remaining})')

    def _apply_effects(self, user_id: Any, voucher: dict[str, Any]) -> None:
        amount = _dec(voucher.get('amount'))
        if voucher.get('type') == 'receipt':
            self._db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) + ? WHERE id=?", (str(amount), user_id))
        elif voucher.get('type') in ('payment', 'expense'):
            self._db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) - ? WHERE id=?", (str(amount), user_id))
        if voucher.get('customer_id'):
            self._db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS REAL) - ? WHERE id=? AND user_id=?", (str(amount), voucher['customer_id'], user_id))
        elif voucher.get('supplier_id'):
            self._db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS REAL) - ? WHERE id=? AND user_id=?", (str(amount), voucher['supplier_id'], user_id))
        if voucher.get('invoice_id'):
            self._db.execute("UPDATE invoices SET paid = CAST(COALESCE(paid, '0') AS REAL) + ? WHERE id=? AND user_id=?", (str(amount), voucher['invoice_id'], user_id))

    def _reverse_effects(self, user_id: Any, voucher: dict[str, Any]) -> None:
        amount = _dec(voucher.get('amount'))
        if voucher.get('type') == 'receipt':
            self._db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) - ? WHERE id=?", (str(amount), user_id))
        elif voucher.get('type') in ('payment', 'expense'):
            self._db.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS REAL) + ? WHERE id=?", (str(amount), user_id))
        if voucher.get('customer_id'):
            self._db.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS REAL) + ? WHERE id=? AND user_id=?", (str(amount), voucher['customer_id'], user_id))
        elif voucher.get('supplier_id'):
            self._db.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS REAL) + ? WHERE id=? AND user_id=?", (str(amount), voucher['supplier_id'], user_id))
        if voucher.get('invoice_id'):
            self._db.execute("UPDATE invoices SET paid = CAST(COALESCE(paid, '0') AS REAL) - ? WHERE id=? AND user_id=?", (str(amount), voucher['invoice_id'], user_id))

    def _record_movement(self, user_id: Any, voucher_id: int, voucher: dict[str, Any]) -> None:
        self._db.execute("DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type='voucher' AND reference_id=?", (user_id, voucher_id))
        amount = _dec(voucher.get('amount'))
        signed = abs(amount) if voucher.get('type') == 'receipt' else -abs(amount)
        self._db.execute('''
            INSERT INTO cash_bank_movements
            (user_id, branch_id, cashbox_id, bank_account_id, movement_type, amount, direction, reference_type, reference_id, description, movement_date, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
        ''', (
            user_id, voucher.get('branch_id'), voucher.get('cashbox_id'), voucher.get('bank_account_id'), voucher.get('type'),
            str(signed), 'in' if signed >= 0 else 'out', 'voucher', voucher_id,
            voucher.get('description') or voucher.get('reference') or 'سند مالي', voucher.get('date')
        ))

    def _delete_movement(self, user_id: Any, voucher_id: int) -> None:
        self._db.execute("DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type='voucher' AND reference_id=?", (user_id, voucher_id))

    def create_voucher(self, user_id: Any, data: dict[str, Any]) -> int:
        self.validate_payload(user_id, data)
        self._db.execute("BEGIN TRANSACTION")
        try:
            cursor = self._db.execute('''
                INSERT INTO vouchers
                (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id,
                 exchange_rate_to_usd, original_currency, branch_id, cashbox_id, bank_account_id, payment_method)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                user_id, data['type'], data['date'], str(data['amount']),
                data.get('description', ''), data.get('reference', ''),
                data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
                data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'), data.get('branch_id'),
                data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method', 'cash')
            ))
            voucher_id = int(cursor.lastrowid)
            self._apply_effects(user_id, data)
            self._record_movement(user_id, voucher_id, data)
            self._db.execute("COMMIT")
            return voucher_id
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def update_voucher(self, user_id: Any, voucher_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        self.validate_payload(user_id, data, exclude_voucher_id=voucher_id)
        self._db.execute("BEGIN TRANSACTION")
        try:
            old_row = self._db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
            if not old_row:
                self._db.execute("ROLLBACK")
                return None
            old = dict(old_row)
            self._reverse_effects(user_id, old)
            self._db.execute('''
                UPDATE vouchers
                SET type=?, date=?, amount=?, description=?, reference=?, customer_id=?, supplier_id=?, invoice_id=?,
                    exchange_rate_to_usd=?, original_currency=?, branch_id=?, cashbox_id=?, bank_account_id=?, payment_method=?
                WHERE id=? AND user_id=?
            ''', (
                data['type'], data['date'], str(data['amount']), data.get('description', ''), data.get('reference', ''),
                data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
                data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'), data.get('branch_id'),
                data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method', 'cash'), voucher_id, user_id
            ))
            self._apply_effects(user_id, data)
            self._record_movement(user_id, voucher_id, data)
            self._db.execute("COMMIT")
            return old
        except Exception:
            try:
                self._db.execute("ROLLBACK")
            except Exception:
                pass
            raise

    def delete_voucher(self, user_id: Any, voucher_id: int) -> dict[str, Any] | None:
        self._db.execute("BEGIN TRANSACTION")
        try:
            old_row = self._db.execute("SELECT * FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id)).fetchone()
            if not old_row:
                self._db.execute("ROLLBACK")
                return None
            old = dict(old_row)
            self._reverse_effects(user_id, old)
            self._delete_movement(user_id, voucher_id)
            self._db.execute("DELETE FROM vouchers WHERE id=? AND user_id=?", (voucher_id, user_id))
            self._db.execute("COMMIT")
            return old
        except Exception:
            try:
                self._db.execute("ROLLBACK")
            except Exception:
                pass
            raise


def get_voucher_repository() -> VoucherRepository:
    return VoucherRepository()
