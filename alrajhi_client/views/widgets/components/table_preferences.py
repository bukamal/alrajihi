# -*- coding: utf-8 -*-
"""Small wrapper around QSettings for table layout persistence."""
from PyQt5.QtCore import QSettings


class TablePreferences:
    def __init__(self, namespace='tables'):
        self.settings = QSettings('Alrajhi', 'Accounting')
        self.namespace = namespace

    def key(self, identity, part):
        safe_identity = identity or 'default'
        return f'{self.namespace}/{safe_identity}/{part}'

    def save_state(self, identity, state):
        self.settings.setValue(self.key(identity, 'header_state'), state)

    def load_state(self, identity):
        return self.settings.value(self.key(identity, 'header_state'))

    def reset(self, identity):
        self.settings.remove(self.key(identity, 'header_state'))
