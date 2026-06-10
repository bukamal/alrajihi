# -*- coding: utf-8 -*-
from database.repositories.invoice_repo import InvoiceRepository
from typing import List, Dict, Tuple

class InvoiceDAO:
    def __init__(self):
        self.repo = InvoiceRepository()
    
    def get_all(self, search: str = None, inv_type: str = None,
                start_date: str = None, end_date: str = None,
                customer_id: int = None, supplier_id: int = None,
                limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        return self.repo.get_all(search, inv_type, start_date, end_date, customer_id, supplier_id, limit, offset)
    
    def get_by_id(self, invoice_id: int) -> Dict:
        return self.repo.get_by_id(invoice_id)
    
    def create_invoice(self, data: Dict) -> int:
        return self.repo.create_invoice(data)
    
    def update_invoice(self, invoice_id: int, data: Dict):
        self.repo.update_invoice(invoice_id, data)
    
    def delete_invoice(self, invoice_id: int):
        self.repo.delete_invoice(invoice_id)
    
    def get_next_reference(self, inv_type: str) -> str:
        return self.repo.get_next_reference(inv_type)

invoice_dao = InvoiceDAO()


