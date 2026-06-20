# -*- coding: utf-8 -*-
from database.connection import DatabaseConnection
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from auth.session import UserSession
import datetime
from core.item_types import is_finished_product

class ManufacturingDAO:
    def __init__(self):
        self.db = DatabaseConnection()
    
    # ========== Manufacturing hardening helpers ==========
    def _to_decimal(self, value, default='0') -> Decimal:
        try:
            return Decimal(str(value if value is not None else default))
        except Exception:
            return Decimal(str(default))

    def _table_exists(self, table_name: str) -> bool:
        try:
            row = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
            return bool(row)
        except Exception:
            return False

    def _get_item_qty(self, item_id: int) -> Decimal:
        row = self.db.execute("SELECT CAST(quantity AS REAL) as qty FROM items WHERE id=?", (item_id,)).fetchone()
        return self._to_decimal(row['qty']) if row else Decimal('0')

    def _get_item_average_cost(self, item_id: int) -> Decimal:
        row = self.db.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=?", (item_id,)).fetchone()
        return self._to_decimal(row['avg_cost']) if row else Decimal('0')

    def _validate_positive_qty(self, value, label: str) -> Decimal:
        qty = self._to_decimal(value)
        if qty <= 0:
            raise ValueError(f"{label} يجب أن تكون أكبر من صفر")
        return qty

    def _unit_factor(self, item_id, unit_id, fallback='1') -> Decimal:
        """Return the selected unit conversion factor for an item.

        Manufacturing stores operational quantities in base units, but the UI
        may enter component quantities in a secondary unit. This helper keeps
        BOM, reservations, consumptions, and outputs aligned with the material
        unit system used by invoices/POS.
        """
        if unit_id:
            try:
                row = self.db.execute(
                    "SELECT conversion_factor FROM item_units WHERE id=? AND item_id=?",
                    (unit_id, item_id),
                ).fetchone()
                if row:
                    val = self._to_decimal(row['conversion_factor'], fallback)
                    return val if val > 0 else Decimal(str(fallback))
            except Exception:
                pass
        val = self._to_decimal(fallback, '1')
        return val if val > 0 else Decimal('1')

    def _unit_name(self, item_id, unit_id, fallback='') -> str:
        if unit_id:
            try:
                row = self.db.execute(
                    "SELECT unit_name FROM item_units WHERE id=? AND item_id=?",
                    (unit_id, item_id),
                ).fetchone()
                if row:
                    return row['unit_name'] or fallback or ''
            except Exception:
                pass
        return fallback or ''

    def _manufacturing_line_unit_payload(self, line: Dict, qty_key: str = 'quantity') -> Dict:
        item_id = line.get('item_id')
        unit_id = line.get('unit_id')
        qty = self._to_decimal(line.get(qty_key, line.get('qty', '0')))
        factor = self._to_decimal(line.get('conversion_factor') or '0')
        if factor <= 0:
            factor = self._unit_factor(item_id, unit_id, '1')
        base_qty = self._to_decimal(line.get('base_qty') or line.get('quantity_in_base') or line.get(f'{qty_key}_base_qty') or '0')
        if base_qty <= 0 and qty > 0:
            base_qty = qty * factor
        return {
            'unit_id': unit_id,
            'unit_name': self._unit_name(item_id, unit_id, line.get('unit_name') or line.get('unit') or ''),
            'conversion_factor': factor,
            'base_qty': base_qty,
            'barcode_scope': line.get('barcode_scope') or ('unit' if unit_id else 'base'),
            'matched_barcode': line.get('matched_barcode') or line.get('barcode') or '',
        }

    def _validate_bom_payload(self, bom_data: Dict):
        product_id = bom_data.get('product_id')
        if not product_id:
            raise ValueError("يجب اختيار المنتج النهائي")
        self._validate_positive_qty(bom_data.get('quantity', 0), "كمية BOM")
        product = self.db.execute("SELECT id, item_type FROM items WHERE id=?", (product_id,)).fetchone()
        if not product:
            raise ValueError("المنتج النهائي غير موجود")
        if not is_finished_product(product['item_type']):
            raise ValueError("يجب أن يكون المنتج من نوع منتج نهائي")
        lines = bom_data.get('lines') or []
        if not lines:
            raise ValueError("لا يمكن حفظ BOM بدون مكونات")
        seen = set()
        for line in lines:
            item_id = line.get('item_id')
            if not item_id:
                raise ValueError("يوجد مكون بدون مادة")
            if item_id == product_id:
                raise ValueError("لا يمكن أن يكون المنتج النهائي مكوناً لنفسه")
            qty = self._validate_positive_qty(line.get('quantity', 0), "كمية المكون")
            waste = self._to_decimal(line.get('waste_percent', 0))
            if waste < 0:
                raise ValueError("نسبة الهالك لا يمكن أن تكون سالبة")
            unit_id = line.get('unit_id')
            if unit_id:
                unit = self.db.execute("SELECT id FROM item_units WHERE id=? AND item_id=?", (unit_id, item_id)).fetchone()
                if not unit:
                    raise ValueError("الوحدة المحددة لا تتبع مادة المكون في BOM")
            key = (item_id, unit_id)
            if key in seen:
                raise ValueError("يوجد مكون مكرر في BOM")
            seen.add(key)


    # ========== Warehouse integration helpers ==========
    def _default_warehouse_id(self):
        try:
            from core.services.warehouse_service import warehouse_service
            return warehouse_service.default_warehouse_id()
        except Exception:
            return None

    def _warehouse_available_qty(self, item_id: int, warehouse_id=None) -> Decimal:
        try:
            from core.services.warehouse_service import warehouse_service
            return self._to_decimal(warehouse_service.available_qty(item_id, warehouse_id))
        except Exception:
            return self._get_item_qty(item_id)

    def _record_warehouse_movement(self, item_id, warehouse_id, movement_type, quantity, unit_cost, reference_id, notes=''):
        if not warehouse_id:
            return
        try:
            from core.services.warehouse_service import warehouse_service
            warehouse_service.record_movement(item_id, warehouse_id, movement_type, quantity, unit_cost, 'production_order', reference_id, notes)
        except Exception as exc:
            raise ValueError(str(exc))

    def _record_ledger_entry(self, item_id, warehouse_id, movement_type, direction, quantity, unit_cost, reference_type, reference_id, source_table=None, source_id=None, notes=''):
        """Shadow-post local manufacturing effects to Inventory Ledger."""
        try:
            from database.dao.inventory_ledger_dao import inventory_ledger_dao
            return inventory_ledger_dao.record_entry(
                item_id=item_id, movement_type=movement_type, direction=direction,
                quantity=abs(self._to_decimal(quantity)), unit_cost=self._to_decimal(unit_cost),
                warehouse_id=warehouse_id, reference_type=reference_type, reference_id=reference_id,
                source_table=source_table, source_id=source_id, notes=notes
            )
        except Exception as exc:
            raise ValueError(f"فشل تسجيل دفتر المخزون للتصنيع: {exc}")

    def _post_consumption_ledger(self, order, item_id, qty, unit_cost, source_id=None, notes='دفتر مخزون استهلاك إنتاج'):
        return self._record_ledger_entry(
            item_id, order.get('raw_warehouse_id'), 'production_consume', 'out',
            qty, unit_cost, 'production_order', order.get('id'), 'production_consumptions', source_id, notes
        )

    def _post_output_ledger(self, order, item_id, qty, unit_cost, source_id=None, notes='دفتر مخزون إنتاج منتج نهائي'):
        return self._record_ledger_entry(
            item_id, order.get('output_warehouse_id'), 'production_out', 'in',
            qty, unit_cost, 'production_order', order.get('id'), 'production_outputs', source_id, notes
        )

    def _post_consumption_reversal_ledger(self, order, item_id, qty, unit_cost, source_id=None, notes='عكس دفتر مخزون استهلاك إنتاج'):
        return self._record_ledger_entry(
            item_id, order.get('raw_warehouse_id'), 'production_consume_reversal', 'in',
            qty, unit_cost, 'production_order_reversal', order.get('id'), 'production_consumptions', source_id, notes
        )

    def _post_output_reversal_ledger(self, order, item_id, qty, unit_cost, source_id=None, notes='عكس دفتر مخزون إنتاج منتج نهائي'):
        return self._record_ledger_entry(
            item_id, order.get('output_warehouse_id'), 'production_out_reversal', 'out',
            qty, unit_cost, 'production_order_reversal', order.get('id'), 'production_outputs', source_id, notes
        )

    # ========== BOM ==========
    def get_all_boms(self, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        uid = UserSession.get_current_user_id()
        if self.db.is_remote():
            return self.db.get_rest_client().get_boms(limit, offset)
        # وضع محلي
        conn = self.db.get_connection()
        # إجمالي العدد
        total = conn.execute("SELECT COUNT(*) FROM bom WHERE user_id = ?", (uid,)).fetchone()[0]
        # البيانات
        query = """
            SELECT b.*, i.name as product_name 
            FROM bom b
            JOIN items i ON b.product_id = i.id
            WHERE b.user_id = ?
            ORDER BY b.id DESC
        """
        params = [uid]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def get_bom(self, bom_id: int) -> Optional[Dict]:
        uid = UserSession.get_current_user_id()
        if self.db.is_remote():
            return self.db.get_rest_client().get_bom(bom_id)
        row = self.db.execute("""
            SELECT b.*, i.name as product_name 
            FROM bom b
            JOIN items i ON b.product_id = i.id
            WHERE b.id = ? AND b.user_id = ?
        """, (bom_id, uid)).fetchone()
        if not row:
            return None
        bom = dict(row)
        lines = self.db.execute("""
            SELECT bl.*, i.name as item_name,
                   COALESCE(u.unit_name, '') as unit_name,
                   CAST(COALESCE(bl.conversion_factor, u.conversion_factor, 1) AS TEXT) as conversion_factor,
                   CAST(COALESCE(NULLIF(bl.base_qty, ''), CAST(bl.quantity AS REAL) * COALESCE(bl.conversion_factor, u.conversion_factor, 1)) AS TEXT) as base_qty
            FROM bom_lines bl
            JOIN items i ON bl.item_id = i.id
            LEFT JOIN item_units u ON bl.unit_id = u.id AND u.item_id = bl.item_id
            WHERE bl.bom_id = ?
        """, (bom_id,)).fetchall()
        bom['lines'] = [dict(line) for line in lines]
        return bom

    def get_bom_for_product(self, product_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_bom_for_product(product_id)
        uid = UserSession.get_current_user_id()
        row = self.db.execute("SELECT id FROM bom WHERE product_id = ? AND user_id = ?", (product_id, uid)).fetchone()
        if row:
            return self.get_bom(row['id'])
        return None

    def save_bom(self, bom_data: Dict) -> int:
        if self.db.is_remote():
            return self.db.get_rest_client().save_bom(bom_data)
        self._validate_bom_payload(bom_data)
        uid = UserSession.get_current_user_id()
        now = datetime.datetime.now().isoformat()
        if bom_data.get('id'):
            self.db.execute("""
                UPDATE bom SET product_id=?, quantity=?, updated_at=?
                WHERE id=? AND user_id=?
            """, (bom_data['product_id'], str(bom_data['quantity']), now, bom_data['id'], uid))
            self.db.execute("DELETE FROM bom_lines WHERE bom_id=?", (bom_data['id'],))
            bom_id = bom_data['id']
        else:
            cur = self.db.execute("""
                INSERT INTO bom (product_id, quantity, user_id, created_at, updated_at)
                VALUES (?,?,?,?,?)
            """, (bom_data['product_id'], str(bom_data['quantity']), uid, now, now))
            bom_id = cur.lastrowid
        for line in bom_data.get('lines', []):
            self.db.execute("""
                INSERT INTO bom_lines (bom_id, item_id, quantity, unit_id, conversion_factor, base_qty, barcode_scope, matched_barcode, waste_percent)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (bom_id, line['item_id'], str(line['quantity']), line.get('unit_id'), str(self._manufacturing_line_unit_payload(line)['conversion_factor']), str(self._manufacturing_line_unit_payload(line)['base_qty']), self._manufacturing_line_unit_payload(line)['barcode_scope'], self._manufacturing_line_unit_payload(line)['matched_barcode'], str(line.get('waste_percent', 0))))
        self.db.commit()
        return bom_id

    def delete_bom(self, bom_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().delete_bom(bom_id)
            return True, ''
        uid = UserSession.get_current_user_id()
        rows = self.db.execute("""
            SELECT id, status FROM production_orders 
            WHERE product_id = (SELECT product_id FROM bom WHERE id = ?) 
            AND user_id = ? AND status IN ('planned', 'in_progress')
        """, (bom_id, uid)).fetchall()
        if rows:
            return False, f"لا يمكن حذف BOM لوجود أوامر إنتاج نشطة: {', '.join(str(r['id']) for r in rows)}"
        self.db.execute("DELETE FROM bom WHERE id=? AND user_id=?", (bom_id, uid))
        self.db.commit()
        return True, ""

    # ========== BOM متعدد المستويات ==========
    def _bom_line_required_base_qty(self, bom: Dict, line: Dict, planned_qty: Decimal) -> Decimal:
        """Return the component quantity in the component base unit.

        BOM line quantity is expressed for bom.quantity units of the parent
        product. If a secondary unit is selected, item_units.conversion_factor
        converts that line quantity into the item's base unit. waste_percent is
        stored as a ratio (10% = 0.10), matching bom_dialog.py.
        """
        bom_qty = self._validate_positive_qty(bom.get('quantity', 1), "كمية BOM")
        line_qty = self._validate_positive_qty(line.get('quantity', 0), "كمية المكون")
        conversion_factor = self._to_decimal(line.get('conversion_factor') or '1')
        if conversion_factor <= 0:
            conversion_factor = Decimal('1')
        waste_factor = Decimal('1') + self._to_decimal(line.get('waste_percent', 0))
        return line_qty * conversion_factor * (planned_qty / bom_qty) * waste_factor

    def _expand_bom(self, product_id: int, quantity: Decimal, multiplier: Decimal = Decimal('1'), visited: set = None) -> List[Dict]:
        if visited is None:
            visited = set()
        if product_id in visited:
            raise Exception(f"دورة في BOM: المنتج {product_id} يظهر مرتين")
        visited.add(product_id)
        bom = self.get_bom_for_product(product_id)
        if not bom:
            raise Exception(f"المنتج {product_id} ليس له قائمة مواد (BOM)")
        result = []
        for line in bom.get('lines', []):
            item_id = line['item_id']
            item = self.db.execute("SELECT item_type FROM items WHERE id=?", (item_id,)).fetchone()
            required_qty = self._bom_line_required_base_qty(bom, line, quantity)
            if item and is_finished_product(item['item_type']):
                sub_items = self._expand_bom(item_id, required_qty, multiplier, visited)
                result.extend(sub_items)
            else:
                result.append({
                    'item_id': item_id,
                    'item_name': line.get('item_name', ''),
                    'required_qty': required_qty,
                    'waste_percent': Decimal(str(line.get('waste_percent', 0))),
                    'unit_id': line.get('unit_id'),
                    'unit_name': line.get('unit_name', ''),
                    'conversion_factor': Decimal(str(line.get('conversion_factor') or '1'))
                })
        visited.remove(product_id)
        return result

    def get_required_materials_recursive(self, product_id: int, planned_qty: Decimal, warehouse_id=None) -> List[Dict]:
        raw_materials = self._expand_bom(product_id, planned_qty)
        merged = {}
        for mat in raw_materials:
            key = mat['item_id']
            if key in merged:
                merged[key]['required_qty'] += mat['required_qty']
            else:
                merged[key] = mat
        result = []
        for mat in merged.values():
            available = self._warehouse_available_qty(mat['item_id'], warehouse_id)
            mat['available_qty'] = available
            mat['is_sufficient'] = available >= mat['required_qty']
            result.append(mat)
        return result

    # ========== حجوزات المواد ==========
    def create_reservations(self, order_id: int, required_materials: List[Dict]):
        if self.db.is_remote():
            return
        for mat in required_materials:
            self.db.execute("""
                INSERT INTO material_reservations (order_id, item_id, reserved_qty, consumed_qty, unit_id, unit_name, conversion_factor, reserved_base_qty, consumed_base_qty, barcode_scope)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (order_id, mat['item_id'], str(mat['required_qty']), '0', mat.get('unit_id'), mat.get('unit_name', ''), str(mat.get('conversion_factor') or '1'), str(mat.get('base_qty') or mat.get('required_qty')), '0', mat.get('barcode_scope') or ('unit' if mat.get('unit_id') else 'base')))
        self.db.commit()

    def get_reservations(self, order_id: int) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_reservations(order_id)
        rows = self.db.execute("""
            SELECT r.*, i.name as item_name, COALESCE(r.unit_name, u.unit_name, '') AS unit_name
            FROM material_reservations r
            JOIN items i ON r.item_id = i.id
            LEFT JOIN item_units u ON u.id = r.unit_id AND u.item_id = r.item_id
            WHERE r.order_id = ?
            ORDER BY r.id
        """, (order_id,)).fetchall()
        return [dict(row) for row in rows]

    def update_reservation_consumed(self, order_id: int, item_id: int, consumed_qty: Decimal):
        self.db.execute("""
            UPDATE material_reservations 
            SET consumed_qty = CAST(consumed_qty AS REAL) + ?,
                consumed_base_qty = CAST(COALESCE(consumed_base_qty, 0) AS REAL) + ?
            WHERE order_id = ? AND item_id = ?
        """, (str(consumed_qty), str(consumed_qty), order_id, item_id))
        self.db.commit()

    # ========== أوامر الإنتاج ==========
    def get_all_production_orders(self, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        uid = UserSession.get_current_user_id()
        if self.db.is_remote():
            return self.db.get_rest_client().get_production_orders(limit, offset)
        conn = self.db.get_connection()
        total = conn.execute("SELECT COUNT(*) FROM production_orders WHERE user_id = ?", (uid,)).fetchone()[0]
        query = """
            SELECT po.*, i.name as product_name,
                   rw.name AS raw_warehouse_name, ow.name AS output_warehouse_name
            FROM production_orders po
            JOIN items i ON po.product_id = i.id
            LEFT JOIN warehouses rw ON rw.id = po.raw_warehouse_id
            LEFT JOIN warehouses ow ON ow.id = po.output_warehouse_id
            WHERE po.user_id = ?
            ORDER BY po.id DESC
        """
        params = [uid]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def get_production_order(self, order_id: int) -> Optional[Dict]:
        uid = UserSession.get_current_user_id()
        row = self.db.execute("""
            SELECT po.*, i.name as product_name,
                   rw.name AS raw_warehouse_name, ow.name AS output_warehouse_name
            FROM production_orders po
            JOIN items i ON po.product_id = i.id
            LEFT JOIN warehouses rw ON rw.id = po.raw_warehouse_id
            LEFT JOIN warehouses ow ON ow.id = po.output_warehouse_id
            WHERE po.id = ? AND po.user_id = ?
        """, (order_id, uid)).fetchone()
        if not row:
            return None
        order = dict(row)
        order['consumptions'] = [dict(r) for r in self.db.execute("SELECT * FROM production_consumptions WHERE order_id=?", (order_id,)).fetchall()]
        order['outputs'] = [dict(r) for r in self.db.execute("SELECT * FROM production_outputs WHERE order_id=?", (order_id,)).fetchall()]
        order['reservations'] = [dict(r) for r in self.db.execute("SELECT * FROM material_reservations WHERE order_id=?", (order_id,)).fetchall()]
        return order

    def create_production_order(self, product_id: int, planned_qty: Decimal, notes: str = '', raw_warehouse_id=None, output_warehouse_id=None) -> int:
        if self.db.is_remote():
            return self.db.get_rest_client().create_production_order({
                'product_id': product_id,
                'planned_qty': str(planned_qty),
                'notes': notes,
                'raw_warehouse_id': raw_warehouse_id,
                'output_warehouse_id': output_warehouse_id,
            })
        planned_qty = self._validate_positive_qty(planned_qty, "الكمية المخططة")
        uid = UserSession.get_current_user_id()
        now = datetime.datetime.now().isoformat()
        bom = self.get_bom_for_product(product_id)
        if not bom or not bom.get('lines'):
            raise ValueError("لا يمكن إنشاء أمر إنتاج دون BOM صالح يحتوي على مكونات")
        raw_warehouse_id = raw_warehouse_id or self._default_warehouse_id()
        output_warehouse_id = output_warehouse_id or self._default_warehouse_id()
        if not raw_warehouse_id or not output_warehouse_id:
            raise ValueError("يجب وجود مستودع مواد خام ومستودع منتج نهائي")
        required = self.get_required_materials_recursive(product_id, planned_qty, raw_warehouse_id)
        insufficient = [m for m in required if not m.get('is_sufficient')]
        if insufficient:
            details = "\n".join(f"{m.get('item_name','')}: المطلوب {m.get('required_qty')}، المتوفر {m.get('available_qty')}" for m in insufficient)
            raise ValueError("لا يمكن إنشاء أمر الإنتاج لعدم كفاية المواد:\n" + details)
        year = datetime.datetime.now().strftime("%Y%m%d")
        cur = self.db.execute("SELECT order_number FROM production_orders ORDER BY id DESC LIMIT 1")
        last = cur.fetchone()
        if last:
            parts = last['order_number'].split('-')
            num = int(parts[1]) + 1 if len(parts) == 2 and parts[0] == year else 1
        else:
            num = 1
        order_number = f"{year}-{num:04d}"
        cur = self.db.execute("""
            INSERT INTO bom_snapshots (order_number, product_id, product_name, created_at)
            VALUES (?,?,?,?)
        """, (order_number, product_id, bom.get('product_name', ''), now))
        snapshot_id = cur.lastrowid
        for line in bom.get('lines', []):
            self.db.execute("""
                INSERT INTO bom_snapshot_lines (snapshot_id, item_id, item_name, quantity, unit_name, unit_id, conversion_factor, base_qty, barcode_scope, matched_barcode, waste_percent)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (snapshot_id, line['item_id'], line.get('item_name', ''), str(line['quantity']), line.get('unit_name', ''), line.get('unit_id'), str(line.get('conversion_factor') or '1'), str(line.get('base_qty') or self._bom_line_required_base_qty(bom, line, self._to_decimal(bom.get('quantity', 1)))), line.get('barcode_scope') or ('unit' if line.get('unit_id') else 'base'), line.get('matched_barcode') or '', str(line.get('waste_percent', 0))))
        cur = self.db.execute("""
            INSERT INTO production_orders (order_number, product_id, planned_qty, status, user_id, created_at, notes, bom_snapshot_id, raw_warehouse_id, output_warehouse_id)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (order_number, product_id, str(planned_qty), 'planned', uid, now, notes, snapshot_id, raw_warehouse_id, output_warehouse_id))
        order_id = cur.lastrowid
        self.create_reservations(order_id, required)
        self.db.commit()
        return order_id

    def start_production(self, order_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().start_production(order_id)
            return True, ''
        order = self.get_production_order(order_id)
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] != 'planned':
            return False, f"لا يمكن بدء أمر بحالة {order['status']}"
        if self._to_decimal(order.get('planned_qty')) <= 0:
            return False, "الكمية المخططة يجب أن تكون أكبر من صفر"
        reservations = self.get_reservations(order_id)
        if not reservations:
            try:
                required = self.get_required_materials_recursive(order['product_id'], self._to_decimal(order['planned_qty']))
                if not required:
                    return False, "لا توجد مواد مطلوبة للأمر"
                self.create_reservations(order_id, required)
                reservations = self.get_reservations(order_id)
            except Exception as e:
                return False, f"لا يمكن إنشاء حجوزات المواد: {e}"
        insufficient = []
        for r in reservations:
            required_qty = self._to_decimal(r.get('reserved_qty')) - self._to_decimal(r.get('consumed_qty'))
            available = self._warehouse_available_qty(r['item_id'], order.get('raw_warehouse_id'))
            if available < required_qty:
                insufficient.append(f"{r['item_name']}: المطلوب {required_qty}، المتوفر {available}")
        if insufficient:
            return False, "المواد التالية غير كافية:\n" + "\n".join(insufficient)
        self.db.execute("UPDATE production_orders SET status='in_progress', start_date=? WHERE id=?", (datetime.datetime.now().isoformat(), order_id))
        self.db.commit()
        return True, ""

    def cancel_production(self, order_id: int):
        if self.db.is_remote():
            return self.db.get_rest_client().cancel_production(order_id)
        self.db.execute("UPDATE production_orders SET status='cancelled', end_date=? WHERE id=?", (datetime.datetime.now().isoformat(), order_id))
        self.db.commit()
        self.db.execute("DELETE FROM material_reservations WHERE order_id=?", (order_id,))
        self.db.commit()

    def consume_material(self, order_id: int, item_id: int, consumed_qty: Decimal, unit_cost: Decimal) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().consume_material(order_id, item_id, str(consumed_qty), str(unit_cost))
            return True, ''
        order = self.get_production_order(order_id)
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] != 'in_progress':
            return False, f"لا يمكن تسجيل استهلاك لأمر بحالة {order['status']}"
        consumed_qty = self._to_decimal(consumed_qty)
        if consumed_qty <= 0:
            return False, "كمية الاستهلاك يجب أن تكون أكبر من صفر"
        unit_cost = self._to_decimal(unit_cost)
        if unit_cost < 0:
            return False, "تكلفة الوحدة لا يمكن أن تكون سالبة"
        if unit_cost == 0:
            unit_cost = self._get_item_average_cost(item_id)
        reservation = self.db.execute("""
            SELECT reserved_qty, consumed_qty, unit_id, unit_name, conversion_factor, barcode_scope FROM material_reservations 
            WHERE order_id = ? AND item_id = ?
        """, (order_id, item_id)).fetchone()
        if not reservation:
            return False, "لا يوجد حجز لهذه المادة في هذا الأمر"
        reserved = self._to_decimal(reservation['reserved_qty'])
        consumed_sofar = self._to_decimal(reservation['consumed_qty'])
        remaining = reserved - consumed_sofar
        if consumed_qty > remaining:
            return False, f"الكمية المستهلكة ({consumed_qty}) تتجاوز المتبقي من الحجز ({remaining})"
        available = self._warehouse_available_qty(item_id, order.get('raw_warehouse_id'))
        if available < consumed_qty:
            return False, f"المخزون غير كافٍ. المطلوب {consumed_qty}، المتوفر {available}"
        self.db.execute("""
            UPDATE material_reservations 
            SET consumed_qty = CAST(consumed_qty AS REAL) + ?,
                consumed_base_qty = CAST(COALESCE(consumed_base_qty, 0) AS REAL) + ?
            WHERE order_id = ? AND item_id = ?
        """, (str(consumed_qty), str(consumed_qty), order_id, item_id))
        now = datetime.datetime.now().isoformat()
        cur = self.db.execute("""
            INSERT INTO production_consumptions (order_id, item_id, consumed_qty, unit_id, unit_name, conversion_factor, consumed_base_qty, barcode_scope, unit_cost, movement_date)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (order_id, item_id, str(consumed_qty), reservation['unit_id'], reservation['unit_name'] or '', str(reservation['conversion_factor'] or '1'), str(consumed_qty), reservation['barcode_scope'] or ('unit' if reservation['unit_id'] else 'base'), str(unit_cost), now))
        consumption_id = getattr(cur, 'lastrowid', None)
        self._record_inventory_movement(item_id, 'production_consume', consumed_qty, unit_cost, order_id)
        self._record_warehouse_movement(item_id, order.get('raw_warehouse_id'), 'production_consume_out', -consumed_qty, unit_cost, order_id, 'استهلاك مواد أمر إنتاج')
        self.db.commit()
        return True, ""

    def complete_production(self, order_id: int, produced_qty: Decimal) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().complete_production(order_id, str(produced_qty))
            return True, ''
        order = self.get_production_order(order_id)
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] != 'in_progress':
            return False, f"لا يمكن إتمام أمر بحالة {order['status']}"
        produced_qty = self._to_decimal(produced_qty)
        if produced_qty <= 0:
            return False, "كمية الإنتاج يجب أن تكون أكبر من صفر"
        reservations = self.get_reservations(order_id)
        if not reservations:
            return False, "لا توجد حجوزات مواد لهذا الأمر"
        for r in reservations:
            remaining = self._to_decimal(r['reserved_qty']) - self._to_decimal(r['consumed_qty'])
            if remaining > Decimal('0.001'):
                return False, f"لم يتم استهلاك كامل كمية المادة {r['item_name']}. المتبقي: {remaining:.2f}"
        consumptions = self.db.execute("SELECT consumed_qty, unit_cost FROM production_consumptions WHERE order_id=?", (order_id,)).fetchall()
        if not consumptions:
            return False, "لا يمكن إتمام الإنتاج دون تسجيل استهلاك مواد"
        total_cost = sum(self._to_decimal(c['consumed_qty']) * self._to_decimal(c['unit_cost']) for c in consumptions)
        if total_cost <= 0:
            return False, "تكلفة الإنتاج يجب أن تكون أكبر من صفر"
        unit_cost = total_cost / produced_qty
        now = datetime.datetime.now().isoformat()
        cur = self.db.execute("""
            INSERT INTO production_outputs (order_id, item_id, produced_qty, unit_id, unit_name, conversion_factor, produced_base_qty, barcode_scope, unit_cost, output_date)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (order_id, order['product_id'], str(produced_qty), None, '', '1', str(produced_qty), 'base', str(unit_cost), now))
        output_id = getattr(cur, 'lastrowid', None)
        self._record_inventory_movement(order['product_id'], 'production_out', produced_qty, unit_cost, order_id)
        self._record_warehouse_movement(order['product_id'], order.get('output_warehouse_id'), 'production_output_in', produced_qty, unit_cost, order_id, 'إدخال منتج نهائي من أمر إنتاج')
        new_produced = self._to_decimal(order.get('produced_qty', 0)) + produced_qty
        self.db.execute("""
            UPDATE production_orders SET produced_qty=?, status='completed', end_date=?
            WHERE id=?
        """, (str(new_produced), now, order_id))
        entry_id = self._create_journal_entry(
            date=now,
            description=f"إتمام أمر إنتاج {order['order_number']}",
            ref_type='production_completion',
            ref_id=order_id,
            lines=[
                {'account': 'inventory', 'debit': total_cost, 'credit': Decimal('0')},
                {'account': 'raw_materials', 'debit': Decimal('0'), 'credit': total_cost}
            ]
        )
        self.db.execute("UPDATE production_orders SET linked_entry_id=?, linked_entry_type='production_completion' WHERE id=?", (entry_id, order_id))
        self.db.commit()
        return True, ""

    def delete_production_order(self, order_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().delete_production_order(order_id)
            return True, ''
        order = self.get_production_order(order_id)
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] not in ('planned', 'cancelled'):
            return False, f"لا يمكن حذف أمر بحالة {order['status']}"
        self.db.execute("DELETE FROM production_consumptions WHERE order_id=?", (order_id,))
        self.db.execute("DELETE FROM production_outputs WHERE order_id=?", (order_id,))
        self.db.execute("DELETE FROM material_reservations WHERE order_id=?", (order_id,))
        self.db.execute("DELETE FROM production_orders WHERE id=?", (order_id,))
        self.db.commit()
        return True, ""

    # ========== دوال مساعدة ==========
    def _record_inventory_movement(self, item_id, movement_type, quantity, unit_cost, reference_id):
        uid = UserSession.get_current_user_id()
        now = datetime.datetime.now().isoformat()
        self.db.execute("""
            INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
            VALUES (?,?,?,?,?,?,?)
        """, (item_id, uid, movement_type, str(quantity), str(unit_cost), reference_id, now))
        self._update_item_quantity(item_id)
        if movement_type in ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse'):
            self._recalculate_average_cost(item_id)

    def _update_item_quantity(self, item_id):
        cur = self.db.execute("""
            SELECT SUM(
                CASE 
                    WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse') 
                    THEN CAST(quantity AS REAL)
                    WHEN movement_type IN ('sale','production_consume','purchase_return') 
                    THEN -CAST(quantity AS REAL)
                    ELSE 0
                END
            ) as total_qty
            FROM inventory_movements
            WHERE item_id = ?
        """, (item_id,))
        row = cur.fetchone()
        new_qty = Decimal(str(row[0])) if row[0] else Decimal('0')
        self.db.execute("UPDATE items SET quantity = ? WHERE id = ?", (str(new_qty), item_id))
        self.db.commit()

    def _recalculate_average_cost(self, item_id):
        cur = self.db.execute("""
            SELECT 
                SUM(CAST(quantity AS REAL)) as total_qty,
                SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) as total_cost
            FROM inventory_movements
            WHERE item_id = ? AND movement_type IN ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse')
        """, (item_id,))
        row = cur.fetchone()
        total_qty = Decimal(str(row[0])) if row[0] else Decimal('0')
        total_cost = Decimal(str(row[1])) if row[1] else Decimal('0')
        avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
        self.db.execute("UPDATE items SET average_cost = ? WHERE id = ?", (str(avg), item_id))
        self.db.commit()

    def _journal_columns(self, table: str) -> set:
        try:
            return {str(row[1]) for row in self.db.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            return set()

    def _ensure_accounting_schema(self) -> None:
        """Keep manufacturing accounting optional but schema-compatible.

        Older manufacturing code wrote to legacy columns (date/reference_type and
        entry_id/account_code).  The current accounting module owns the canonical
        journal schema (entry_date/source_type/source_id and
        journal_entry_id/account_id).  This helper upgrades/initializes that schema
        before manufacturing tries to post an optional accounting entry.
        """
        try:
            from gateways.local.accounting_gateway import LocalAccountingGateway
            LocalAccountingGateway().ensure_schema(self.db.get_connection())
        except Exception:
            pass

    def _next_journal_entry_no(self) -> str:
        try:
            row = self.db.execute('SELECT COALESCE(MAX(id),0)+1 FROM journal_entries').fetchone()
            n = row[0] if row else 1
            return f'JE-{int(n):06d}'
        except Exception:
            return f"JE-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _account_id(self, code: str):
        row = self.db.execute('SELECT id FROM accounts WHERE code=?', (code,)).fetchone()
        if row:
            return int(row['id'] if hasattr(row, 'keys') else row[0])
        return None

    def _manufacturing_account_code(self, account_name: str) -> str:
        # Current chart does not split finished/raw inventory accounts, so both
        # map to the inventory account while preserving balanced posting.
        mapping = {
            'inventory': '1200',
            'raw_materials': '1200',
            'raw_material': '1200',
            'manufacturing_variance': '5000',
        }
        return mapping.get(str(account_name or '').strip(), '1200')

    def _create_journal_entry(self, date, description, ref_type, ref_id, lines):
        # Accounting posting is optional for manufacturing completion; inventory
        # and warehouse ledgers are the operational source of truth.  If the
        # accounting schema is unavailable or incompatible, do not block production.
        self._ensure_accounting_schema()
        if not (self._table_exists('journal_entries') and self._table_exists('journal_lines')):
            return None
        entry_cols = self._journal_columns('journal_entries')
        line_cols = self._journal_columns('journal_lines')
        now = datetime.datetime.now().isoformat()
        try:
            if {'entry_date', 'source_type', 'source_id'}.issubset(entry_cols):
                existing = self.db.execute(
                    "SELECT id FROM journal_entries WHERE source_type=? AND source_id=?",
                    (ref_type, ref_id)
                ).fetchone()
                if existing:
                    return int(existing['id'] if hasattr(existing, 'keys') else existing[0])
                cur = self.db.execute("""
                    INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'POSTED', ?)
                """, (self._next_journal_entry_no(), str(date)[:10], ref_type, ref_id, description, now))
                entry_id = int(cur.lastrowid)
                if {'journal_entry_id', 'account_id'}.issubset(line_cols):
                    for line in lines:
                        account_id = self._account_id(self._manufacturing_account_code(line.get('account')))
                        if not account_id:
                            continue
                        self.db.execute(
                            "INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)",
                            (entry_id, account_id, str(line.get('debit') or 0), str(line.get('credit') or 0), description)
                        )
                elif {'entry_id', 'account_code'}.issubset(line_cols):
                    for line in lines:
                        self.db.execute("INSERT INTO journal_lines(entry_id, account_code, debit, credit) VALUES (?,?,?,?)", (entry_id, line.get('account'), str(line.get('debit') or 0), str(line.get('credit') or 0)))
                self.db.commit()
                return entry_id
            if {'date', 'reference_type', 'reference_id'}.issubset(entry_cols):
                cur = self.db.execute("""
                    INSERT INTO journal_entries (date, description, reference_type, reference_id, created_at)
                    VALUES (?,?,?,?,?)
                """, (date, description, ref_type, ref_id, now))
                entry_id = cur.lastrowid
                for line in lines:
                    self.db.execute("""
                        INSERT INTO journal_lines (entry_id, account_code, debit, credit)
                        VALUES (?,?,?,?)
                    """, (entry_id, line['account'], str(line['debit']), str(line['credit'])))
                self.db.commit()
                return entry_id
        except Exception as exc:
            try:
                print(f"⚠️ تم تخطي قيد التصنيع المحاسبي الاختياري: {exc}")
            except Exception:
                pass
            return None
        return None

    def _reverse_journal_entry(self, entry_id):
        if not entry_id or not (self._table_exists('journal_entries') and self._table_exists('journal_lines')):
            return
        self._ensure_accounting_schema()
        entry_cols = self._journal_columns('journal_entries')
        line_cols = self._journal_columns('journal_lines')
        now = datetime.datetime.now().isoformat()
        try:
            if {'journal_entry_id', 'account_id'}.issubset(line_cols) and {'entry_date', 'source_type', 'source_id'}.issubset(entry_cols):
                lines = self.db.execute("SELECT account_id, debit, credit, memo FROM journal_lines WHERE journal_entry_id=?", (entry_id,)).fetchall()
                if not lines:
                    return
                cur = self.db.execute("""
                    INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_at)
                    VALUES (?, ?, 'reversal', ?, ?, 'POSTED', ?)
                """, (self._next_journal_entry_no(), now[:10], entry_id, f"عكس قيد رقم {entry_id}", now))
                reverse_entry_id = int(cur.lastrowid)
                for line in lines:
                    self.db.execute("INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)", (reverse_entry_id, line['account_id'], str(line['credit']), str(line['debit']), line['memo']))
                self.db.commit()
                return
            if {'entry_id', 'account_code'}.issubset(line_cols) and {'date', 'reference_type', 'reference_id'}.issubset(entry_cols):
                lines = self.db.execute("SELECT account_code, debit, credit FROM journal_lines WHERE entry_id=?", (entry_id,)).fetchall()
                if not lines:
                    return
                cur = self.db.execute("""
                    INSERT INTO journal_entries (date, description, reference_type, reference_id, created_at)
                    VALUES (?,?,?,?,?)
                """, (now, f"عكس قيد رقم {entry_id}", 'reversal', entry_id, now))
                reverse_entry_id = cur.lastrowid
                for line in lines:
                    self.db.execute("""
                        INSERT INTO journal_lines (entry_id, account_code, debit, credit)
                        VALUES (?,?,?,?)
                    """, (reverse_entry_id, line['account_code'], str(line['credit']), str(line['debit'])))
                self.db.commit()
        except Exception as exc:
            try:
                print(f"⚠️ تم تخطي عكس قيد التصنيع المحاسبي الاختياري: {exc}")
            except Exception:
                pass

    # ========== دوال التوافق ==========
    def get_consumptions(self, order_id: int) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_consumptions(order_id)
        rows = self.db.execute("""
            SELECT pc.*, i.name as item_name, COALESCE(pc.unit_name, u.unit_name, '') AS unit_name
            FROM production_consumptions pc
            JOIN items i ON pc.item_id = i.id
            LEFT JOIN item_units u ON u.id = pc.unit_id AND u.item_id = pc.item_id
            WHERE pc.order_id = ?
            ORDER BY pc.id
        """, (order_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_outputs(self, order_id: int) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_outputs(order_id)
        rows = self.db.execute("""
            SELECT po.*, i.name as item_name, COALESCE(po.unit_name, u.unit_name, '') AS unit_name
            FROM production_outputs po
            JOIN items i ON po.item_id = i.id
            LEFT JOIN item_units u ON u.id = po.unit_id AND u.item_id = po.item_id
            WHERE po.order_id = ?
            ORDER BY po.id
        """, (order_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_required_materials(self, bom_id: int, planned_qty: Decimal) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_required_materials(bom_id, str(planned_qty))
        bom = self.get_bom(bom_id)
        if not bom:
            return []
        # Use the same recursive expansion as production orders/availability so
        # direct BOM previews cannot understate requirements in multi-level BOMs.
        materials = self.get_required_materials_recursive(bom['product_id'], self._to_decimal(planned_qty))
        for mat in materials:
            mat['available_qty'] = Decimal('0')
            mat['is_sufficient'] = False
        return materials

    def check_materials_availability(self, bom_id: int, planned_qty: Decimal) -> Tuple[bool, List[Dict]]:
        if self.db.is_remote():
            return self.db.get_rest_client().check_materials_availability(bom_id, str(planned_qty))
        required = self.get_required_materials(bom_id, planned_qty)
        for mat in required:
            item = self.db.execute("SELECT CAST(quantity AS REAL) as qty FROM items WHERE id=?", (mat['item_id'],)).fetchone()
            mat['available_qty'] = Decimal(str(item['qty'])) if item else Decimal('0')
            mat['is_sufficient'] = mat['available_qty'] >= mat['required_qty']
        all_sufficient = all(mat['is_sufficient'] for mat in required)
        return all_sufficient, required

    def can_edit_bom(self, bom_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            return self.db.get_rest_client().can_edit_bom(bom_id)
        bom = self.get_bom(bom_id)
        if not bom:
            return False, "BOM غير موجود"
        orders = self.db.execute("""
            SELECT id, status FROM production_orders 
            WHERE product_id = ? AND status IN ('planned', 'in_progress')
        """, (bom['product_id'],)).fetchall()
        if orders:
            return False, f"لا يمكن تعديل BOM لوجود أوامر إنتاج نشطة: {', '.join(str(o['id']) for o in orders)}"
        return True, ""

    def delete_consumption(self, consumption_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().delete_consumption(consumption_id)
            return True, ''
        row = self.db.execute("SELECT * FROM production_consumptions WHERE id=?", (consumption_id,)).fetchone()
        if not row:
            return False, "الاستهلاك غير موجود"
        consumption = dict(row)
        order = self.get_production_order(consumption['order_id'])
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] != 'in_progress':
            return False, f"لا يمكن حذف استهلاك من أمر {order['status']}"
        self.db.execute("""
            UPDATE material_reservations 
            SET consumed_qty = CAST(consumed_qty AS REAL) - ?,
                consumed_base_qty = CAST(COALESCE(consumed_base_qty, 0) AS REAL) - ?
            WHERE order_id = ? AND item_id = ?
        """, (consumption['consumed_qty'], consumption.get('consumed_base_qty') or consumption['consumed_qty'], consumption['order_id'], consumption['item_id']))
        qty = self._to_decimal(consumption['consumed_qty'])
        cost = self._to_decimal(consumption['unit_cost'])
        self._record_inventory_movement(consumption['item_id'], 'consumption_reverse', qty, cost, None)
        self._record_warehouse_movement(consumption['item_id'], order.get('raw_warehouse_id'), 'production_consume_reverse_in', qty, cost, order['id'], 'عكس استهلاك مادة إنتاج')
        self.db.execute("DELETE FROM production_consumptions WHERE id=?", (consumption_id,))
        self.db.commit()
        return True, ""

    def delete_output(self, output_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().delete_output(output_id)
            return True, ''
        row = self.db.execute("SELECT * FROM production_outputs WHERE id=?", (output_id,)).fetchone()
        if not row:
            return False, "الإنتاج غير موجود"
        output = dict(row)
        order = self.get_production_order(output['order_id'])
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] == 'completed':
            return False, "لا يمكن حذف مخرج من أمر مكتمل؛ استخدم التراجع عن الإنتاج بالكامل"
        if order['status'] != 'in_progress':
            return False, f"لا يمكن حذف إنتاج من أمر {order['status']}"
        produced_qty = Decimal(str(output['produced_qty']))
        available = self._get_item_qty(output['item_id'])
        if available < produced_qty:
            return False, f"لا يمكن حذف الإنتاج لأن مخزون المنتج سيصبح سالباً. المتوفر {available}، المطلوب عكسه {produced_qty}"
        cost = self._to_decimal(output['unit_cost'])
        self._record_inventory_movement(output['item_id'], 'adjustment', -produced_qty, cost, None)
        self._record_warehouse_movement(output['item_id'], order.get('output_warehouse_id'), 'production_output_reverse_out', -produced_qty, cost, order['id'], 'عكس مخرج إنتاج')
        self.db.execute("DELETE FROM production_outputs WHERE id=?", (output_id,))
        new_produced = Decimal(str(order['produced_qty'])) - Decimal(str(output['produced_qty']))
        self.db.execute("UPDATE production_orders SET produced_qty=? WHERE id=?", (str(new_produced), order['id']))
        self.db.commit()
        return True, ""

    def reverse_production_order(self, order_id: int) -> Tuple[bool, str]:
        if self.db.is_remote():
            self.db.get_rest_client().reverse_production_order(order_id)
            return True, ''
        order = self.get_production_order(order_id)
        if not order:
            return False, "أمر الإنتاج غير موجود"
        if order['status'] not in ('in_progress', 'completed'):
            return False, f"لا يمكن التراجع عن أمر {order['status']}"
        outputs = self.get_outputs(order_id)
        for o in outputs:
            produced_qty = Decimal(str(o['produced_qty']))
            available = self._get_item_qty(o['item_id'])
            if available < produced_qty:
                return False, f"لا يمكن التراجع لأن مخزون المنتج {o.get('item_name', o['item_id'])} سيصبح سالباً. المتوفر {available}، المطلوب عكسه {produced_qty}"
        self.db.begin()
        try:
            if order.get('linked_entry_id'):
                self._reverse_journal_entry(order['linked_entry_id'])
            consumptions = self.get_consumptions(order_id)
            for c in consumptions:
                qty = self._to_decimal(c['consumed_qty'])
                cost = self._to_decimal(c['unit_cost'])
                self._record_inventory_movement(c['item_id'], 'adjustment', qty, cost, None)
                self._record_warehouse_movement(c['item_id'], order.get('raw_warehouse_id'), 'production_consume_reverse_in', qty, cost, order_id, 'عكس استهلاك أمر إنتاج')
            outputs = self.get_outputs(order_id)
            for o in outputs:
                qty = self._to_decimal(o['produced_qty'])
                cost = self._to_decimal(o['unit_cost'])
                self._record_inventory_movement(o['item_id'], 'adjustment', -qty, cost, None)
                self._record_warehouse_movement(o['item_id'], order.get('output_warehouse_id'), 'production_output_reverse_out', -qty, cost, order_id, 'عكس مخرج أمر إنتاج')
            self.db.execute("DELETE FROM production_consumptions WHERE order_id=?", (order_id,))
            self.db.execute("DELETE FROM production_outputs WHERE order_id=?", (order_id,))
            self.db.execute("DELETE FROM material_reservations WHERE order_id=?", (order_id,))
            self.db.execute("DELETE FROM production_orders WHERE id=?", (order_id,))
            self.db.commit()
            return True, "تم التراجع عن أمر الإنتاج بالكامل"
        except Exception as e:
            self.db.rollback()
            return False, f"حدث خطأ أثناء التراجع: {str(e)}"

manufacturing_dao = ManufacturingDAO()


