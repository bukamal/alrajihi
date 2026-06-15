from pathlib import Path
root = Path(__file__).resolve().parents[1]
config = (root/'alrajhi_client/config.py').read_text(encoding='utf-8')
dashboard = (root/'alrajhi_client/views/widgets/dashboard_widget.py').read_text(encoding='utf-8')
prints = (root/'alrajhi_client/printing/print_templates.py').read_text(encoding='utf-8')
assert '_default_logo_path' in config and 'company/logo_path' in config, 'Company logo default fallback missing'
assert '_create_company_info_panel' in dashboard and 'معلومات الشركة' in dashboard, 'Dashboard company info card missing'
assert 'logo_png' in dashboard and 'get_company_info' in dashboard, 'Dashboard card is not connected to brand/company settings'
assert "<html dir='{doc_dir}'" in prints and "direction: {doc_dir}" in prints and '_document_direction()' in prints, 'HTML print direction must follow active language direction'
assert 'logo_png(512)' in prints, 'Print templates do not fall back to branded logo'
print('phase61_brand_print_dashboard_guard: PASS')
