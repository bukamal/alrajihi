# -*- coding: utf-8 -*-
from database.repositories.supplier_repo import SupplierRepository

class SupplierDAO:
    def __init__(self):
        self.repo = SupplierRepository()
    
    def get_all(self, search=None, limit=None, offset=None):
        return self.repo.get_all(search, limit, offset)

    def get_suppliers(self, search=None, limit=None, offset=None):
        """Compatibility alias for code that names the collection explicitly."""
        return self.get_all(search, limit, offset)
    
    def get_by_id(self, sid):
        return self.repo.get_by_id(sid)
    
    def add(self, name, phone='', address=''):
        return self.repo.add(name, phone, address)
    
    def update(self, sid, name, phone, address):
        self.repo.update(sid, name, phone, address)
    
    def delete(self, sid):
        self.repo.delete(sid)
    
    def update_balance(self, sid, delta):
        self.repo.update_balance(sid, delta)

supplier_dao = SupplierDAO()


