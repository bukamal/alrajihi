# -*- coding: utf-8 -*-
from database.repositories.branch_repo import BranchRepository


class BranchDAO:
    def __init__(self):
        self.repo = BranchRepository()

    def bootstrap_defaults(self):
        return self.repo.bootstrap_defaults()

    def get_all(self, include_archived=False):
        return self.repo.list_branches(include_archived=include_archived)

    def get_by_id(self, branch_id):
        return self.repo.get_by_id(branch_id)

    def add(self, data):
        return self.repo.add(data)

    def update(self, branch_id, data):
        return self.repo.update(branch_id, data)

    def delete(self, branch_id):
        return self.repo.archive(branch_id)

    def default_branch_id(self):
        return self.repo.default_branch_id()

    def set_default(self, branch_id):
        return self.repo.set_default(branch_id)

    def diagnostics(self):
        return self.repo.branch_diagnostics()


branch_dao = BranchDAO()
