# -*- coding: utf-8 -*-
from database.repositories.warehouse_repo import WarehouseRepository


class WarehouseDAO:
    def __init__(self):
        self.repo = WarehouseRepository()

    def bootstrap_defaults(self):
        return self.repo.bootstrap_defaults()

    def get_all(self, include_archived=False):
        return self.repo.list_warehouses(include_archived=include_archived)

    def get_by_id(self, warehouse_id):
        return self.repo.get_by_id(warehouse_id)

    def add(self, data):
        return self.repo.add(data)

    def update(self, warehouse_id, data):
        return self.repo.update(warehouse_id, data)

    def delete(self, warehouse_id):
        return self.repo.archive(warehouse_id)

    def balances(self, search=None, warehouse_id=None, limit=None, offset=None):
        return self.repo.balances(search=search, warehouse_id=warehouse_id, limit=limit, offset=offset)

    def balance_count(self, search=None, warehouse_id=None):
        return self.repo.balance_count(search=search, warehouse_id=warehouse_id)

    def movements(self, item_id=None, warehouse_id=None, limit=100):
        return self.repo.movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit)

    def default_warehouse_id(self):
        return self.repo.default_warehouse_id()

    def default_warehouse(self):
        return self.repo.default_warehouse()

    def available_qty(self, item_id, warehouse_id=None, variant_id=None):
        return self.repo.available_qty(item_id, warehouse_id, variant_id=variant_id)

    def record_movement(self, item_id, warehouse_id, movement_type, quantity, unit_cost='0', reference_type=None, reference_id=None, notes='', **variant_data):
        return self.repo.record_movement(item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes, **variant_data)

    def reverse_reference(self, reference_type, reference_id):
        return self.repo.reverse_reference(reference_type, reference_id)

    def create_transfer(self, data):
        return self.repo.create_transfer(data)

    def cancel_transfer(self, transfer_id):
        return self.repo.cancel_transfer(transfer_id)

    def transfers(self, limit=200):
        return self.repo.transfers(limit=limit)


warehouse_dao = WarehouseDAO()
