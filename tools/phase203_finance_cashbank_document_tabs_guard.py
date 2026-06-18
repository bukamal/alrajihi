# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(__file__).resolve().parents[1]
checks = []
checks.append((root/'alrajhi_client/features/finance/documents/cashbox_document_tab.py').exists())
checks.append((root/'alrajhi_client/features/finance/documents/bank_account_document_tab.py').exists())
checks.append('class CashboxDocumentTab' in (root/'alrajhi_client/features/finance/documents/cashbox_document_tab.py').read_text(encoding='utf-8'))
checks.append('class BankAccountDocumentTab' in (root/'alrajhi_client/features/finance/documents/bank_account_document_tab.py').read_text(encoding='utf-8'))
policy = (root/'alrajhi_client/core/services/finance_operation_policy.py').read_text(encoding='utf-8')
checks.append('OP_CASHBOX_CREATE' in policy and 'OP_BANK_CREATE' in policy and 'finance_operation_policy' in policy)
svc = (root/'alrajhi_client/core/services/cashbox_service.py').read_text(encoding='utf-8')
checks.append('cashbox_by_id' in svc and 'bank_account_by_id' in svc)
checks.append('OP_CASHBOX_CREATE' in svc and 'OP_BANK_EDIT' in svc)
main = (root/'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
checks.append('open_cashbox_document' in main and 'open_bank_account_document' in main)
widget = (root/'alrajhi_client/views/widgets/cashboxes_widget.py').read_text(encoding='utf-8')
checks.append('open_cashbox_document' in widget and 'open_bank_account_document' in widget)
checks.append('current_source_row' in widget)
checks.append('finance_operation_policy' in widget)
settings = (root/'alrajhi_client/core/services/settings_service.py').read_text(encoding='utf-8')
checks.append('def get_finance_settings' in settings)
perms = (root/'alrajhi_client/core/services/permission_service.py').read_text(encoding='utf-8')
checks.append('ACTION_USE_FINANCE' in perms and 'ACTION_CASHBOX_CREATE' in perms and 'ACTION_BANK_CREATE' in perms)
tr = (root/'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')
checks.append('cashbox_document_new' in tr and 'bank_account_document_new' in tr and 'phase203_finance_cashbank_document_tabs' in tr)
if not all(checks):
    raise SystemExit('Phase203 finance cash/bank document tab guard failed')
print('phase203_finance_cashbank_document_tabs_guard passed')
