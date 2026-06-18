#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks = []

def read(rel):
    return (root/rel).read_text(encoding='utf-8')

checks.append(('user_operation_policy exists', (root/'alrajhi_client/core/services/user_operation_policy.py').exists()))
checks.append(('user document tab exists', (root/'alrajhi_client/features/users/documents/user_document_tab.py').exists()))
checks.append(('features users export exists', (root/'alrajhi_client/features/users/__init__.py').exists()))
main=read('alrajhi_client/views/main_window.py')
checks.append(('main window open_user_document', 'def open_user_document' in main and 'UserDocumentTab' in main))
users=read('alrajhi_client/views/widgets/users_widget.py')
checks.append(('users widget opens tab', 'open_user_document' in users and 'UserDialog(self)' in users))
checks.append(('users widget source row safe', 'current_source_row' in users and '_selected_source_row' in users))
svc=read('alrajhi_client/core/services/user_service.py')
checks.append(('user service policy protected', 'user_operation_policy' in svc and 'OP_CREATE' in svc and 'OP_EDIT' in svc and 'OP_CHANGE_PASSWORD' in svc))
settings=read('alrajhi_client/core/services/settings_service.py')
checks.append(('user settings contract', 'def get_user_settings' in settings and "users/operations/allow_create" in settings))
perm=read('alrajhi_client/core/services/permission_service.py')
checks.append(('users manage permission action', 'ACTION_USERS_MANAGE' in perm and "'users.manage'" in perm))
tr=read('alrajhi_client/i18n/translator.py')
checks.append(('user translations', 'user_document_new' in tr and 'users.operation.create' in tr))
failed=[name for name, ok in checks if not ok]
if failed:
    for f in failed:
        print('FAILED:', f)
    raise SystemExit(1)
print('phase206_user_document_governance_guard passed')
