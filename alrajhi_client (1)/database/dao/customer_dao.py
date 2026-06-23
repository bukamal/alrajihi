# -*- coding: utf-8 -*-
from database.repositories.customer_repo import CustomerRepository

class CustomerDAO:
    def __init__(self):
        self.repo = CustomerRepository()
    
    def get_all(self, search=None, limit=None, offset=None):
        return self.repo.get_all(search, limit, offset)

    def get_customers(self, search=None, limit=None, offset=None):
        """Compatibility alias for code that names the collection explicitly."""
        return self.get_all(search, limit, offset)
    
    def get_by_id(self, cid):
        return self.repo.get_by_id(cid)
    
    def add(self, name, phone='', address=''):
        return self.repo.add(name, phone, address)
    
    def update(self, cid, name, phone, address):
        self.repo.update(cid, name, phone, address)
    
    def delete(self, cid):
        self.repo.delete(cid)
    
    def update_balance(self, cid, delta):
        self.repo.update_balance(cid, delta)

customer_dao = CustomerDAO()


