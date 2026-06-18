# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def require(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    branch_tab = read('alrajhi_client/features/branches/documents/branch_document_tab.py')
    branches_widget = read('alrajhi_client/views/widgets/branches_widget.py')
    main_window = read('alrajhi_client/views/main_window.py')
    service = read('alrajhi_client/core/services/branch_service.py')
    policy = read('alrajhi_client/core/services/branch_operation_policy.py')
    settings = read('alrajhi_client/core/services/settings_service.py')
    tr = read('alrajhi_client/i18n/translator.py')

    require('class BranchDocumentTab(BaseDocumentTab)' in branch_tab, 'BranchDocumentTab must inherit BaseDocumentTab')
    require('branch_service.add_branch' in branch_tab and 'branch_service.update_branch' in branch_tab, 'BranchDocumentTab must save via BranchService')
    require('branch_operation_policy.require' in branch_tab, 'BranchDocumentTab must enforce branch operation policy')
    require('open_branch_document' in main_window and 'BranchDocumentTab' in main_window, 'MainWindow must expose open_branch_document')
    require('open_branch_document' in branches_widget, 'BranchesWidget must prefer the tabbed branch document')
    require('BranchDialog(self)' in branches_widget, 'Legacy BranchDialog fallback must remain available')
    require('current_source_row' in branches_widget, 'BranchesWidget selected id must be source-row safe')
    require("'⭐ تعيين كفرع افتراضي'" not in branches_widget, 'Default branch button label must not be hard-coded')
    for method, op in [
        ('add_branch', 'OP_CREATE'),
        ('update_branch', 'OP_EDIT'),
        ('archive_branch', 'OP_ARCHIVE'),
        ('set_default_branch', 'OP_SET_DEFAULT'),
    ]:
        require(method in service and op in service, f'BranchService.{method} must enforce {op}')
    require('class BranchOperationPolicy' in policy and 'branch_operation_policy = BranchOperationPolicy()' in policy, 'Branch operation policy singleton missing')
    require('def get_branch_settings' in settings, 'settings_service.get_branch_settings missing')
    for key in ('branch_document_new', 'branch_document_edit', 'branch_name_required', 'set_default_branch_btn', 'default_branch_set'):
        require(key in tr, f'Missing i18n key: {key}')
    print('phase202_branch_document_tab_guard passed')

if __name__ == '__main__':
    main()
