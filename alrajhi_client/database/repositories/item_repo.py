# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from typing import List, Dict, Optional
from core.compat import records

class ItemRepository(BaseRepository):
    def get_items(self, search: str = None, limit: int = None, offset: int = None, user_id: str = None) -> List[Dict]:
        return self.db.get_items(search, limit, offset)
    
    def get_by_id(self, item_id: int) -> Optional[Dict]:
        return self.db.get_item_by_id(item_id)
    
    def add(self, data: Dict, user_id: str) -> int:
        return self.db.add_item(data)
    
    def update(self, item_id: int, data: Dict, user_id: str):
        return self.db.update_item(item_id, data)
    
    def delete(self, item_id: int, user_id: str):
        return self.db.delete_item(item_id)
    
    def get_units(self, item_id: int) -> List[Dict]:
        if self.db.is_remote():
            for it in records(self.get_items(), 'items'):
                if it.get('id') == item_id:
                    return it.get('units', []) or []
            return []
        else:
            conn = self.db.get_connection()
            rows = conn.execute("SELECT id, item_id, unit_name, conversion_factor FROM item_units WHERE item_id=?", (item_id,)).fetchall()
            return [dict(row) for row in rows]
    
    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float) -> int:
        if self.db.is_remote():
            raise NotImplementedError("Use REST for units")
        conn = self.db.get_connection()
        cursor = conn.execute("INSERT INTO item_units (item_id, unit_name, conversion_factor) VALUES (?,?,?)",
                             (item_id, unit_name, conversion_factor))
        conn.commit()
        return cursor.lastrowid
    
    def delete_unit(self, unit_id: int):
        if self.db.is_remote():
            raise NotImplementedError("Use REST for units")
        conn = self.db.get_connection()
        conn.execute("DELETE FROM item_units WHERE id=?", (unit_id,))
        conn.commit()
    
    def clear_units(self, item_id: int):
        if self.db.is_remote():
            raise NotImplementedError("Use REST for units")
        conn = self.db.get_connection()
        conn.execute("DELETE FROM item_units WHERE item_id=?", (item_id,))
        conn.commit()


