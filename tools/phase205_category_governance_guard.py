# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def require(cond, msg):
    if not cond:
        raise SystemExit(msg)

policy = read('alrajhi_client/core/services/category_operation_policy.py')
require('class CategoryOperationPolicy' in policy, 'missing category operation policy')
require('def _settings_service' in policy and 'def _permission_service' in policy, 'policy must lazy-load settings/permissions')

settings = read('alrajhi_client/core/services/settings_service.py')
require('def get_category_settings' in settings, 'missing category settings contract')
require('categories/operations/allow_create' in settings, 'missing category operation switches')

perm = read('alrajhi_client/core/services/permission_service.py')
for token in ['ACTION_CATEGORY_VIEW','ACTION_CATEGORY_CREATE','ACTION_CATEGORY_EDIT','ACTION_CATEGORY_ARCHIVE','ACTION_CATEGORY_RESTORE']:
    require(token in perm, f'missing permission action {token}')

rbac = read('alrajhi_client/core/services/rbac_service.py')
for token in ['categories.view','categories.create','categories.edit','categories.archive','categories.restore']:
    require(token in rbac, f'missing RBAC permission {token}')

service = read('alrajhi_client/core/services/product_service.py')
require('def _category_policy' in service, 'product service must use category policy')
for token in ['OP_CREATE','OP_EDIT','OP_ARCHIVE','OP_RESTORE']:
    require(token in service, f'missing category service operation {token}')

widget = read('alrajhi_client/views/widgets/categories_widget.py')
require('category_operation_policy' in widget, 'categories widget must use policy')
require('current_source_row' in widget or 'mapToSource' in widget, 'categories widget must use source-row safe selection')
require('self.add_btn' in widget, 'add button must be controllable')

tab = read('alrajhi_client/features/categories/category_editor_tab.py')
require('category_operation_policy' in tab, 'category tab must use policy')
require('set_read_only' in read('alrajhi_client/features/categories/components/category_panels.py'), 'category panel must support read-only')

print('phase205_category_governance_guard passed')
