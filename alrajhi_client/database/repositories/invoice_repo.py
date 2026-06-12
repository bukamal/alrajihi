# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from typing import List, Dict, Optional, Tuple

class InvoiceRepository(BaseRepository):
    def get_all(self, search: str = None, inv_type: str = None,
                start_date: str = None, end_date: str = None,
                customer_id: int = None, supplier_id: int = None,
                limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        return self.db.get_invoices(search, inv_type, start_date, end_date, customer_id, supplier_id, limit, offset)

    def get_by_id(self, invoice_id: int) -> Optional[Dict]:
        return self.db.get_invoice_by_id(invoice_id)

    def create_invoice(self, data: Dict) -> int:
        return self.db.add_invoice(data)

    def update_invoice(self, invoice_id: int, data: Dict):
        self.db.update_invoice(invoice_id, data)

    def delete_invoice(self, invoice_id: int):
        self.db.delete_invoice(invoice_id)

    def get_next_reference(self, inv_type: str) -> str:
        if self.db.is_remote():
            return self.db.get_rest_client().get_next_invoice_reference(inv_type)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        year = __import__('datetime').datetime.now().strftime("%Y")
        prefix = f"{inv_type[:3].upper()}-{year}-"
        conn = self.db.get_connection()
        cur = conn.execute("SELECT MAX(reference) FROM invoices WHERE reference LIKE ? AND user_id=?", (prefix + '%', uid))
        max_ref = cur.fetchone()[0]
        if max_ref:
            try:
                num = int(max_ref.split('-')[-1]) + 1
            except:
                num = 1
        else:
            num = 1
        return f"{prefix}{num:04d}"


