# -*- coding: utf-8 -*-
from database.repositories.voucher_repo import VoucherRepository

class VoucherDAO:
    def __init__(self):
        self.repo = VoucherRepository()
    
    def get_all(self, search=None, vtype=None, limit=None, offset=None):
        return self.repo.get_all(search, vtype, limit, offset)
    
    def get_by_id(self, vid):
        return self.repo.get_by_id(vid)
    
    def add(self, data):
        return self.repo.add(data)
    
    def update(self, vid, data):
        return self.repo.update(vid, data)
    
    def delete(self, vid):
        return self.repo.delete(vid)

# إنشاء كائن مفرد للاستخدام المباشر
voucher_dao = VoucherDAO()


