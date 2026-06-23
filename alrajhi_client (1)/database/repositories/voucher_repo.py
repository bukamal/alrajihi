# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from typing import List, Dict, Tuple

class VoucherRepository(BaseRepository):
    def get_all(self, search: str = None, vtype: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        return self.db.get_vouchers(vtype, limit, offset)
    
    def get_by_id(self, voucher_id: int) -> Dict:
        return self.db.get_voucher_by_id(voucher_id)
    
    def add(self, data: Dict) -> int:
        return self.db.add_voucher(data)
    
    def update(self, voucher_id: int, data: Dict):
        self.db.update_voucher(voucher_id, data)
    
    def delete(self, voucher_id: int):
        self.db.delete_voucher(voucher_id)


