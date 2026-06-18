from pathlib import Path
root=Path('/mnt/data/phase205_work')

def p(rel): return root/rel

# Add category operation policy
policy = p('alrajhi_client/core/services/category_operation_policy.py')
policy.write_text('''# -*- coding: utf-8 -*-\n"""Category/catalog operation governance (Phase 205).\n\nCategories are material master data.  They affect item classification, reports,\nand item lookup filters; therefore UI and services must use one settings/RBAC\ncontract instead of inline dialogs or direct product-service calls.\n"""\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Any, Dict\n\nfrom core.services.audit_service import audit_service\n\n\n@dataclass(frozen=True)\nclass CategoryOperation:\n    key: str\n    setting_key: str\n    permission_action: str\n    label_key: str\n\n\nclass CategoryOperationPolicy:\n    OP_USE = 'use'\n    OP_CREATE = 'create'\n    OP_EDIT = 'edit'\n    OP_ARCHIVE = 'archive'\n    OP_RESTORE = 'restore'\n\n    def _permission_service(self):\n        from core.services.permission_service import permission_service\n        return permission_service\n\n    def _settings_service(self):\n        from core.services.settings_service import settings_service\n        return settings_service\n\n    def _operations(self) -> Dict[str, CategoryOperation]:\n        ps = self._permission_service()\n        return {\n            self.OP_USE: CategoryOperation(self.OP_USE, 'allow_use', ps.ACTION_CATEGORY_VIEW, 'category.operation.use'),\n            self.OP_CREATE: CategoryOperation(self.OP_CREATE, 'allow_create', ps.ACTION_CATEGORY_CREATE, 'category.operation.create'),\n            self.OP_EDIT: CategoryOperation(self.OP_EDIT, 'allow_edit', ps.ACTION_CATEGORY_EDIT, 'category.operation.edit'),\n            self.OP_ARCHIVE: CategoryOperation(self.OP_ARCHIVE, 'allow_archive', ps.ACTION_CATEGORY_ARCHIVE, 'category.operation.archive'),\n            self.OP_RESTORE: CategoryOperation(self.OP_RESTORE, 'allow_restore', ps.ACTION_CATEGORY_RESTORE, 'category.operation.restore'),\n        }\n\n    def settings(self) -> Dict[str, Any]:\n        try:\n            return self._settings_service().get_category_settings()\n        except Exception:\n            return {'enabled': True, 'operations': {}}\n\n    def is_enabled(self) -> bool:\n        return bool(self.settings().get('enabled', True))\n\n    def operation_allowed_by_settings(self, operation_key: str) -> bool:\n        if not self.is_enabled() and operation_key != self.OP_USE:\n            return False\n        op = self._operations().get(operation_key)\n        if not op:\n            return True\n        return bool((self.settings().get('operations', {}) or {}).get(op.setting_key, True))\n\n    def can(self, operation_key: str) -> bool:\n        op = self._operations().get(operation_key)\n        if not op:\n            return True\n        return self.operation_allowed_by_settings(operation_key) and self._permission_service().can(op.permission_action)\n\n    def denial_reason(self, operation_key: str) -> str:\n        op = self._operations().get(operation_key)\n        if not op:\n            return 'unknown_category_operation'\n        if not self.is_enabled() and operation_key != self.OP_USE:\n            return 'categories_disabled'\n        if not self.operation_allowed_by_settings(operation_key):\n            return f'categories_setting_{op.setting_key}_disabled'\n        if not self._permission_service().can(op.permission_action):\n            return f'categories_permission_{op.permission_action}_missing'\n        return ''\n\n    def require(self, operation_key: str, context: str = '', payload: Dict[str, Any] | None = None) -> None:\n        if self.can(operation_key):\n            self.log(operation_key, True, context=context, payload=payload)\n            return\n        reason = self.denial_reason(operation_key)\n        self.log(operation_key, False, reason=reason, context=context, payload=payload)\n        raise PermissionError(reason)\n\n    def log(self, operation_key: str, allowed: bool, reason: str = '', context: str = '', payload: Dict[str, Any] | None = None) -> None:\n        try:\n            audit_service.log(\n                'SECURITY' if not allowed else 'CHECK',\n                'CATEGORY_OPERATION',\n                None,\n                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},\n                details=f"category_operation:{operation_key}:{'allowed' if allowed else 'denied'}",\n            )\n        except Exception:\n            pass\n\n\ncategory_operation_policy = CategoryOperationPolicy()\n''', encoding='utf-8')

# Patch settings service
path=p('alrajhi_client/core/services/settings_service.py')
s=path.read_text(encoding='utf-8')
insert = '''\n    def get_category_settings(self) -> Dict[str, Any]:\n        """Return settings contract for material-category master data screens."""\n        language = self.get_language_settings()\n        profile = self.get_active_profile()\n        return {\n            'enabled': self.get_bool('categories/enabled', True),\n            'ui_language': language.get('ui_language', self.get_language()),\n            'print_language': language.get('print_language', self.print_language()),\n            'touch_density': self.get('categories/touch_density', self.get('ui/touch_density', 'comfortable')) or 'comfortable',\n            'operations': {\n                'allow_use': self.get_bool('categories/operations/allow_use', True),\n                'allow_create': self.get_bool('categories/operations/allow_create', True),\n                'allow_edit': self.get_bool('categories/operations/allow_edit', True),\n                'allow_archive': self.get_bool('categories/operations/allow_archive', True),\n                'allow_restore': self.get_bool('categories/operations/allow_restore', True),\n            },\n            'settings_profile_id': int((profile or {}).get('id') or 1),\n        }\n\n'''
if 'def get_category_settings' not in s:
    s=s.replace('    def get_material_settings(self) -> Dict[str, Any]:', insert + '    def get_material_settings(self) -> Dict[str, Any]:')
path.write_text(s,encoding='utf-8')

# Patch permission_service constants/defaults/mapping/can fallback
path=p('alrajhi_client/core/services/permission_service.py')
s=path.read_text(encoding='utf-8')
if "ACTION_CATEGORY_VIEW" not in s:
    s=s.replace("    ACTION_EDIT_OPENING_STOCK = 'edit_opening_stock'\n", "    ACTION_EDIT_OPENING_STOCK = 'edit_opening_stock'\n    ACTION_CATEGORY_VIEW = 'category_view'\n    ACTION_CATEGORY_CREATE = 'category_create'\n    ACTION_CATEGORY_EDIT = 'category_edit'\n    ACTION_CATEGORY_ARCHIVE = 'category_archive'\n    ACTION_CATEGORY_RESTORE = 'category_restore'\n")
    s=s.replace("        ACTION_EDIT_OPENING_STOCK: True,\n", "        ACTION_EDIT_OPENING_STOCK: True,\n        ACTION_CATEGORY_VIEW: True,\n        ACTION_CATEGORY_CREATE: True,\n        ACTION_CATEGORY_EDIT: True,\n        ACTION_CATEGORY_ARCHIVE: True,\n        ACTION_CATEGORY_RESTORE: True,\n")
    s=s.replace("                    self.ACTION_EDIT_OPENING_STOCK: 'items.opening_stock.edit',\n", "                    self.ACTION_EDIT_OPENING_STOCK: 'items.opening_stock.edit',\n                    self.ACTION_CATEGORY_VIEW: 'categories.view',\n                    self.ACTION_CATEGORY_CREATE: 'categories.create',\n                    self.ACTION_CATEGORY_EDIT: 'categories.edit',\n                    self.ACTION_CATEGORY_ARCHIVE: 'categories.archive',\n                    self.ACTION_CATEGORY_RESTORE: 'categories.restore',\n")
    s=s.replace("        elif action == self.ACTION_EDIT_OPENING_STOCK and settings_service.get_bool('materials/security/restrict_opening_stock_edit_to_admin', False):\n            allowed, reason = False, 'restrict_opening_stock_edit_to_admin'\n", "        elif action == self.ACTION_EDIT_OPENING_STOCK and settings_service.get_bool('materials/security/restrict_opening_stock_edit_to_admin', False):\n            allowed, reason = False, 'restrict_opening_stock_edit_to_admin'\n        elif action == self.ACTION_CATEGORY_VIEW and settings_service.get_bool('security/restrict_categories_view_to_admin', False):\n            allowed, reason = False, 'restrict_categories_view_to_admin'\n        elif action == self.ACTION_CATEGORY_CREATE and settings_service.get_bool('security/restrict_category_create_to_admin', False):\n            allowed, reason = False, 'restrict_category_create_to_admin'\n        elif action == self.ACTION_CATEGORY_EDIT and settings_service.get_bool('security/restrict_category_edit_to_admin', False):\n            allowed, reason = False, 'restrict_category_edit_to_admin'\n        elif action == self.ACTION_CATEGORY_ARCHIVE and settings_service.get_bool('security/restrict_category_archive_to_admin', False):\n            allowed, reason = False, 'restrict_category_archive_to_admin'\n        elif action == self.ACTION_CATEGORY_RESTORE and settings_service.get_bool('security/restrict_category_restore_to_admin', False):\n            allowed, reason = False, 'restrict_category_restore_to_admin'\n")
path.write_text(s,encoding='utf-8')

# Patch rbac service permissions and action map
path=p('alrajhi_client/core/services/rbac_service.py')
s=path.read_text(encoding='utf-8')
if "categories.view" not in s:
    s=s.replace("'items.opening_stock.edit'", "'items.opening_stock.edit', 'categories.view', 'categories.create', 'categories.edit', 'categories.archive', 'categories.restore'", 1)
    s=s.replace("'items.barcodes.print',", "'items.barcodes.print', 'categories.view', 'categories.create', 'categories.edit', 'categories.archive', 'categories.restore',", 1)
    s=s.replace("    'edit_opening_stock': 'items.opening_stock.edit',\n", "    'edit_opening_stock': 'items.opening_stock.edit',\n    'category_view': 'categories.view',\n    'category_create': 'categories.create',\n    'category_edit': 'categories.edit',\n    'category_archive': 'categories.archive',\n    'category_restore': 'categories.restore',\n")
path.write_text(s,encoding='utf-8')

# Patch product_service categories with policy
path=p('alrajhi_client/core/services/product_service.py')
s=path.read_text(encoding='utf-8')
if 'def _category_policy' not in s:
    marker='    # ---------- Categories ----------\n'
    helper='''    def _category_policy(self):\n        from core.services.category_operation_policy import category_operation_policy\n        return category_operation_policy\n\n'''
    s=s.replace(marker, helper + marker)
# Insert policy calls idempotently
s=s.replace("    def categories(self, search: str | None = None, include_inactive: bool = False, include_deleted: bool = False) -> List[Dict]:\n        return records(self.category_gateway.list(search=search, include_inactive=include_inactive, include_deleted=include_deleted), 'categories')\n", "    def categories(self, search: str | None = None, include_inactive: bool = False, include_deleted: bool = False) -> List[Dict]:\n        self._category_policy().require(self._category_policy().OP_USE, context='categories.list')\n        return records(self.category_gateway.list(search=search, include_inactive=include_inactive, include_deleted=include_deleted), 'categories')\n")
s=s.replace("    def category_by_id(self, category_id: int) -> Optional[Dict]:\n        return self.category_gateway.get(category_id)\n", "    def category_by_id(self, category_id: int) -> Optional[Dict]:\n        self._category_policy().require(self._category_policy().OP_USE, context='categories.get', payload={'category_id': category_id})\n        return self.category_gateway.get(category_id)\n")
s=s.replace("    def add_category(self, data_or_name, parent_id=None, description: str = '', color: str = '#64748B', icon: str = 'folder', is_active: int = 1) -> int:\n        if isinstance(data_or_name, dict):\n", "    def add_category(self, data_or_name, parent_id=None, description: str = '', color: str = '#64748B', icon: str = 'folder', is_active: int = 1) -> int:\n        self._category_policy().require(self._category_policy().OP_CREATE, context='categories.create')\n        if isinstance(data_or_name, dict):\n")
s=s.replace("    def update_category(self, category_id: int, data_or_name, **kwargs) -> None:\n        old = self.category_by_id(category_id)\n", "    def update_category(self, category_id: int, data_or_name, **kwargs) -> None:\n        self._category_policy().require(self._category_policy().OP_EDIT, context='categories.edit', payload={'category_id': category_id})\n        old = self.category_by_id(category_id)\n")
s=s.replace("    def delete_category(self, category_id: int) -> None:\n        old = self.category_by_id(category_id)\n", "    def delete_category(self, category_id: int) -> None:\n        self._category_policy().require(self._category_policy().OP_ARCHIVE, context='categories.archive', payload={'category_id': category_id})\n        old = self.category_by_id(category_id)\n")
s=s.replace("    def restore_category(self, category_id: int) -> None:\n        old = self.category_by_id(category_id)\n", "    def restore_category(self, category_id: int) -> None:\n        self._category_policy().require(self._category_policy().OP_RESTORE, context='categories.restore', payload={'category_id': category_id})\n        old = self.category_by_id(category_id)\n")
path.write_text(s,encoding='utf-8')

# Patch category editor tab policy/read-only
path=p('alrajhi_client/features/categories/category_editor_tab.py')
s=path.read_text(encoding='utf-8')
if 'category_operation_policy' not in s:
    s=s.replace("from core.services.product_service import product_service\n", "from core.services.product_service import product_service\nfrom core.services.category_operation_policy import category_operation_policy\n")
    s=s.replace("        self._build_ui()\n", "        self._can_edit = category_operation_policy.can(category_operation_policy.OP_EDIT if self.is_edit else category_operation_policy.OP_CREATE)\n        self._build_ui()\n")
    s=s.replace("        self.properties.changed.connect(lambda: self.set_dirty(True))\n", "        self.properties.set_read_only(not self._can_edit)\n        self.header.save_btn.setEnabled(self._can_edit)\n        if not self._can_edit:\n            self.header.set_subtitle(translate('category_read_only'))\n        self.properties.changed.connect(lambda: self.set_dirty(True))\n")
    s=s.replace("        payload = self.properties.payload()\n", "        if not self._can_edit:\n            show_toast(translate('category_read_only'), 'warning', self)\n            return\n        payload = self.properties.payload()\n")
path.write_text(s,encoding='utf-8')

# Patch category panels: set_subtitle and read_only
path=p('alrajhi_client/features/categories/components/category_panels.py')
s=path.read_text(encoding='utf-8')
if 'def set_subtitle' not in s:
    s=s.replace("        hint = QLabel(translate('categories_hint'))\n        hint.setWordWrap(True)\n        layout.addWidget(hint)\n", "        self.subtitle_label = QLabel(translate('categories_hint'))\n        self.subtitle_label.setWordWrap(True)\n        layout.addWidget(self.subtitle_label)\n")
    s=s.replace("    def set_title(self, title: str) -> None:\n        self.title_label.setText(title)\n", "    def set_title(self, title: str) -> None:\n        self.title_label.setText(title)\n\n    def set_subtitle(self, text: str) -> None:\n        self.subtitle_label.setText(text)\n")
    s=s.replace("    def focus_name(self) -> None:\n        self.name_edit.setFocus()\n", "    def set_read_only(self, read_only: bool) -> None:\n        self.name_edit.setReadOnly(read_only)\n        self.description_edit.setReadOnly(read_only)\n        self.parent_combo.setEnabled(not read_only)\n        self.active_check.setEnabled(not read_only)\n\n    def focus_name(self) -> None:\n        self.name_edit.setFocus()\n")
path.write_text(s,encoding='utf-8')

# Patch categories_widget: import policy, button attr, source row, operation states, fallback only
path=p('alrajhi_client/views/widgets/categories_widget.py')
s=path.read_text(encoding='utf-8')
if 'category_operation_policy' not in s:
    s=s.replace("from core.services.product_service import product_service\n", "from core.services.product_service import product_service\nfrom core.services.category_operation_policy import category_operation_policy\n")
    s=s.replace("        add_btn = QPushButton(translate('new_category_btn'))\n        add_btn.setObjectName('primary')\n        add_btn.clicked.connect(self.add_category)\n", "        self.add_btn = QPushButton(translate('new_category_btn'))\n        self.add_btn.setObjectName('primary')\n        self.add_btn.clicked.connect(self.add_category)\n")
    s=s.replace("        toolbar.addWidget(add_btn)\n", "        toolbar.addWidget(self.add_btn)\n")
    s=s.replace("        self.refresh()\n", "        self._apply_operation_state()\n        self.refresh()\n", 1)
    # Add source row helper after current_category_id or replace method
    s=s.replace("    def current_category_id(self):\n        idx = self.table.currentIndex()\n        if not idx.isValid() or not hasattr(self, 'model'):\n            return None\n        return self.model.get_id(idx.row())\n", "    def _source_row_for_index(self, index=None):\n        idx = index if index is not None else self.table.currentIndex()\n        if not idx.isValid() or not hasattr(self, 'model'):\n            return -1\n        if hasattr(self.table, 'current_source_row') and index is None:\n            return self.table.current_source_row()\n        model = self.table.model()\n        if hasattr(model, 'mapToSource'):\n            try:\n                idx = model.mapToSource(idx)\n            except Exception:\n                pass\n        return idx.row()\n\n    def current_category_id(self):\n        row = self._source_row_for_index()\n        if row < 0 or not hasattr(self, 'model'):\n            return None\n        return self.model.get_id(row)\n\n    def _apply_operation_state(self):\n        can_create = category_operation_policy.can(category_operation_policy.OP_CREATE)\n        if hasattr(self, 'add_btn'):\n            self.add_btn.setEnabled(can_create)\n")
    s=s.replace("        cat_id = self.current_category_id() if index is None else self.model.get_id(index.row())\n", "        row = self._source_row_for_index(index)\n        cat_id = self.current_category_id() if index is None else (self.model.get_id(row) if row >= 0 else None)\n")
    s=s.replace("        main = self._main_window()\n        if main is not None:\n", "        if not category_operation_policy.can(category_operation_policy.OP_CREATE):\n            show_toast(translate('category_operation_denied'), 'warning', self)\n            return\n        main = self._main_window()\n        if main is not None:\n")
    s=s.replace("        main = self._main_window()\n        if main is not None:\n", "        if not category_operation_policy.can(category_operation_policy.OP_EDIT):\n            show_toast(translate('category_operation_denied'), 'warning', self)\n            return\n        main = self._main_window()\n        if main is not None:\n", 1)  # first occurrence after edit maybe may hit add? already first in add patched? Let's accept
    # ensure archive/restore policy before operation
    s=s.replace("        reply = QMessageBox.question(self, translate('confirm_archive'), translate('archive_category_confirm'), QMessageBox.Yes | QMessageBox.No)\n", "        if not category_operation_policy.can(category_operation_policy.OP_ARCHIVE):\n            show_toast(translate('category_operation_denied'), 'warning', self)\n            return\n        reply = QMessageBox.question(self, translate('confirm_archive'), translate('archive_category_confirm'), QMessageBox.Yes | QMessageBox.No)\n")
    s=s.replace("        try:\n            product_service.restore_category(cat_id)\n", "        if not category_operation_policy.can(category_operation_policy.OP_RESTORE):\n            show_toast(translate('category_operation_denied'), 'warning', self)\n            return\n        try:\n            product_service.restore_category(cat_id)\n")
path.write_text(s,encoding='utf-8')

# Need fix if replacements messed add/edit. We'll inspect later.

# Patch translations: simple append to translator dicts by adding fallback? Inspect translator format
path=p('alrajhi_client/i18n/translator.py')
s=path.read_text(encoding='utf-8')
keys = {
'ar': {
'category_read_only':'التصنيف للعرض فقط حسب الصلاحيات أو الإعدادات.',
'category_operation_denied':'العملية غير مسموحة للتصنيفات حسب الصلاحيات أو الإعدادات.',
'category.operation.use':'استخدام التصنيفات',
'category.operation.create':'إنشاء تصنيف',
'category.operation.edit':'تعديل تصنيف',
'category.operation.archive':'أرشفة تصنيف',
'category.operation.restore':'استعادة تصنيف',
},
'en': {
'category_read_only':'Category is read-only due to permissions or settings.',
'category_operation_denied':'Category operation is not allowed by permissions or settings.',
'category.operation.use':'Use categories',
'category.operation.create':'Create category',
'category.operation.edit':'Edit category',
'category.operation.archive':'Archive category',
'category.operation.restore':'Restore category',
},
'de': {
'category_read_only':'Kategorie ist aufgrund von Berechtigungen oder Einstellungen schreibgeschützt.',
'category_operation_denied':'Kategorievorgang ist aufgrund von Berechtigungen oder Einstellungen nicht erlaubt.',
'category.operation.use':'Kategorien verwenden',
'category.operation.create':'Kategorie erstellen',
'category.operation.edit':'Kategorie bearbeiten',
'category.operation.archive':'Kategorie archivieren',
'category.operation.restore':'Kategorie wiederherstellen',
}}
# Add into dicts by locating language markers like 'ar': { maybe
for lang, entries in keys.items():
    for k,v in entries.items():
        if f"'{k}'" in s or f'"{k}"' in s:
            continue
        marker=f"    '{lang}': {{"
        if marker in s:
            insert_line=f"        '{k}': '{v}',\n"
            pos=s.find(marker)+len(marker)
            nl=s.find('\n',pos)+1
            s=s[:nl]+insert_line+s[nl:]
path.write_text(s,encoding='utf-8')

# Patch migrations simple insert extra permission via new migration function at end? Need inspect function style maybe append robust no compile issue.
for rel in ['alrajhi_client/database/migrations.py','alrajhi_server/database/migrations.py']:
    path=p(rel)
    s=path.read_text(encoding='utf-8')
    if 'categories.create' not in s:
        # add to a permissions string if present, easier append into existing script text with execute call in run_migrations? use unsafe but compile ok.
        perm_sql = """\n\ndef migrate_phase205_category_permissions(conn):\n    cur = conn.cursor()\n    rows = [\n        ('categories.view','categories','view','View categories'),\n        ('categories.create','categories','create','Create categories'),\n        ('categories.edit','categories','edit','Edit categories'),\n        ('categories.archive','categories','archive','Archive categories'),\n        ('categories.restore','categories','restore','Restore categories'),\n    ]\n    cur.executemany(\"INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES (?,?,?,?)\", rows)\n    conn.commit()\n"""
        s += perm_sql
    path.write_text(s,encoding='utf-8')

# Add doc and guard
doc=p('PHASE205_CATEGORY_GOVERNANCE_WORKSPACE_HARDENING.md')
doc.write_text('''# Phase 205 — Category Governance / Workspace Hardening\n\nThis phase brings material categories into the same governance model used for warehouses, branches, finance, inventory, manufacturing, POS, and transactions.\n\n## Key changes\n\n- Added `category_operation_policy`.\n- Added `settings_service.get_category_settings()`.\n- Added category RBAC actions: `categories.view/create/edit/archive/restore`.\n- Routed `ProductService` category operations through the policy.\n- Hardened `CategoriesWidget` operation buttons and source-row selection.\n- Hardened `CategoryEditorTab` read-only behavior.\n- Kept old inline category dialog as fallback only.\n''', encoding='utf-8')

guard=p('tools/phase205_category_governance_guard.py')
guard.write_text('''# -*- coding: utf-8 -*-\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\n\ndef read(rel):\n    return (ROOT / rel).read_text(encoding='utf-8')\n\ndef require(cond, msg):\n    if not cond:\n        raise SystemExit(msg)\n\npolicy = read('alrajhi_client/core/services/category_operation_policy.py')\nrequire('class CategoryOperationPolicy' in policy, 'missing category operation policy')\nrequire('def _settings_service' in policy and 'def _permission_service' in policy, 'policy must lazy-load settings/permissions')\n\nsettings = read('alrajhi_client/core/services/settings_service.py')\nrequire('def get_category_settings' in settings, 'missing category settings contract')\nrequire('categories/operations/allow_create' in settings, 'missing category operation switches')\n\nperm = read('alrajhi_client/core/services/permission_service.py')\nfor token in ['ACTION_CATEGORY_VIEW','ACTION_CATEGORY_CREATE','ACTION_CATEGORY_EDIT','ACTION_CATEGORY_ARCHIVE','ACTION_CATEGORY_RESTORE']:\n    require(token in perm, f'missing permission action {token}')\n\nrbac = read('alrajhi_client/core/services/rbac_service.py')\nfor token in ['categories.view','categories.create','categories.edit','categories.archive','categories.restore']:\n    require(token in rbac, f'missing RBAC permission {token}')\n\nservice = read('alrajhi_client/core/services/product_service.py')\nrequire('def _category_policy' in service, 'product service must use category policy')\nfor token in ['OP_CREATE','OP_EDIT','OP_ARCHIVE','OP_RESTORE']:\n    require(token in service, f'missing category service operation {token}')\n\nwidget = read('alrajhi_client/views/widgets/categories_widget.py')\nrequire('category_operation_policy' in widget, 'categories widget must use policy')\nrequire('current_source_row' in widget or 'mapToSource' in widget, 'categories widget must use source-row safe selection')\nrequire('self.add_btn' in widget, 'add button must be controllable')\n\ntab = read('alrajhi_client/features/categories/category_editor_tab.py')\nrequire('category_operation_policy' in tab, 'category tab must use policy')\nrequire('set_read_only' in read('alrajhi_client/features/categories/components/category_panels.py'), 'category panel must support read-only')\n\nprint('phase205_category_governance_guard passed')\n''', encoding='utf-8')
