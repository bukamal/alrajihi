# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

checks = []

bridge = ROOT / 'alrajhi_client/features/restaurant/restaurant_printing_bridge.py'
checks.append((bridge.exists(), 'RestaurantPrintingBridge file must exist'))
if bridge.exists():
    b = bridge.read_text(encoding='utf-8')
    checks += [
        ('printing_service' in b, 'Restaurant printing bridge must delegate to printing_service'),
        ('restaurant_operation_policy.require' in b, 'Restaurant printing must pass through operation policy'),
        ('get_restaurant_settings' in b, 'Restaurant printing must use restaurant settings contract'),
        ('restaurant_receipt_print' in b and 'restaurant_kitchen_ticket_print' in b, 'Bridge must support receipt and kitchen ticket printing'),
    ]

ps = read('alrajhi_client/printing/printing_service.py')
checks += [
    ('restaurant_receipt_html' in ps, 'PrintingService must expose restaurant receipt HTML'),
    ('restaurant_receipt_print' in ps, 'PrintingService must expose restaurant receipt print'),
    ('restaurant_kitchen_ticket_print' in ps, 'PrintingService must expose kitchen ticket print'),
]

tpl = read('alrajhi_client/printing/print_templates.py')
checks += [
    ('def restaurant_receipt_html' in tpl, 'Central print templates must include restaurant_receipt_html'),
    ('def restaurant_kitchen_ticket_html' in tpl, 'Central print templates must include restaurant_kitchen_ticket_html'),
    ('restaurant_receipt' in tpl and 'restaurant_kitchen_ticket' in tpl, 'Restaurant print templates must use translatable title keys'),
]

policy = read('alrajhi_client/core/services/restaurant_operation_policy.py')
checks += [
    ('OP_PRINT_RECEIPT' in policy, 'Restaurant operation policy must define receipt print operation'),
    ('OP_PRINT_KITCHEN_TICKET' in policy, 'Restaurant operation policy must define kitchen ticket print operation'),
    ('restaurant/operations/allow_print_receipt' in policy, 'Receipt printing must be settings-controlled'),
    ('restaurant/operations/allow_print_kitchen_ticket' in policy, 'Kitchen ticket printing must be settings-controlled'),
]

settings = read('alrajhi_client/core/services/settings_service.py')
checks += [
    ('allow_print_receipt' in settings, 'Restaurant settings must expose allow_print_receipt'),
    ('allow_print_kitchen_ticket' in settings, 'Restaurant settings must expose allow_print_kitchen_ticket'),
    ('auto_print_receipt_after_checkout' in settings, 'Restaurant settings must expose auto print receipt'),
    ('auto_print_kitchen_ticket' in settings, 'Restaurant settings must expose auto print kitchen ticket'),
]

ui = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
checks += [
    ('restaurant_printing_bridge' in ui, 'Restaurant POS UI must use RestaurantPrintingBridge'),
    ('print_receipt_btn' in ui, 'Restaurant POS UI must expose receipt print button'),
    ('print_kitchen_btn' in ui, 'Restaurant POS UI must expose kitchen ticket print button'),
    ('OP_PRINT_RECEIPT' in ui and 'OP_PRINT_KITCHEN_TICKET' in ui, 'Restaurant print buttons must be governed by operation policy'),
]

translator = read('alrajhi_client/i18n/translator.py')
checks += [
    ('restaurant.print_receipt' in translator, 'Missing restaurant receipt print translation'),
    ('restaurant.print_kitchen_ticket' in translator, 'Missing kitchen ticket print translation'),
    ('restaurant_operation_print_receipt' in translator, 'Missing receipt print operation translation'),
    ('restaurant_operation_print_kitchen_ticket' in translator, 'Missing kitchen ticket print operation translation'),
]

rbac = read('alrajhi_client/core/services/rbac_service.py')
checks += [
    ('restaurant.receipt.print' in rbac, 'RBAC must include restaurant.receipt.print'),
    ('restaurant.kitchen_ticket.print' in rbac, 'RBAC must include restaurant.kitchen_ticket.print'),
]

failed = [msg for ok, msg in checks if not ok]
if failed:
    raise SystemExit('\n'.join(failed))
print('phase183_restaurant_printing_bridge_guard passed')
