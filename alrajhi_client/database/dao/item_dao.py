# -*- coding: utf-8 -*-
from database.repositories.item_repo import ItemRepository
from core.compat import records

class ItemDAO:
    def __init__(self):
        self.repo = ItemRepository()
    
    def get_items(self, search=None, limit=None, offset=None):
        return self.repo.get_items(search, limit, offset)
    
    def get_by_id(self, item_id):
        return self.repo.get_by_id(item_id)
    
    def add(self, data):
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        return self.repo.add(data, uid)
    
    def update(self, item_id, data):
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        return self.repo.update(item_id, data, uid)
    
    def delete(self, item_id):
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        return self.repo.delete(item_id, uid)
    
    def get_units(self, item_id):
        return self.repo.get_units(item_id)
    
    def add_unit(self, item_id, unit_name, conversion_factor):
        return self.repo.add_unit(item_id, unit_name, conversion_factor)
    
    def delete_unit(self, unit_id):
        return self.repo.delete_unit(unit_id)
    
    def clear_units(self, item_id):
        return self.repo.clear_units(item_id)
    
    def get_by_barcode(self, barcode):
        for it in records(self.get_items(), 'items'):
            if it.get('barcode') == barcode:
                return it
        return None

# إنشاء كائن مفرد للاستخدام المباشر
item_dao = ItemDAO()


