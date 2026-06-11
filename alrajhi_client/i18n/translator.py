# -*- coding: utf-8 -*-
"""Centralized UI/printing translations for Alrajhi Accounting.

This module intentionally stays dependency-light.  It is used by startup screens,
login, settings, print templates and any widget that wants translated labels.
Unknown keys fall back to Arabic, then English, then the key itself so old code
continues to work even before every string is migrated.
"""
from __future__ import annotations

from typing import Dict
from contextlib import contextmanager

_current_lang = 'ar'

LANGUAGES: Dict[str, Dict[str, str]] = {
    'ar': {'native_name': 'العربية', 'direction': 'rtl', 'html_lang': 'ar'},
    'en': {'native_name': 'English', 'direction': 'ltr', 'html_lang': 'en'},
    'de': {'native_name': 'Deutsch', 'direction': 'ltr', 'html_lang': 'de'},
}

_translations: Dict[str, Dict[str, str]] = {
    'ar': {
        'app_title': 'الراجحي للمحاسبة',
        'app_subtitle': 'نظام محاسبة ومخزون وتصنيع',
        'secure_login_subtitle': 'تسجيل دخول آمن إلى النظام',
        'connection_mode': 'وضع التشغيل',
        'remote_mode': 'متصل بخادم',
        'local_mode': 'محلي',
        'startup_database': 'قاعدة البيانات',
        'startup_license': 'الترخيص',
        'startup_login': 'تسجيل الدخول',
        'startup_ui': 'الواجهة',
        'startup_init': 'تهيئة بدء التشغيل',
        'startup_loading': 'جاري تهيئة النظام...',
        'startup_do_not_close': 'الرجاء عدم إغلاق التطبيق أثناء التحميل',
        'startup_error_title': 'تعذر إكمال التشغيل',
        'startup_error_detail': 'راجع الرسالة ثم أعد المحاولة.',
        'dashboard': 'لوحة التحكم', 'accounts': 'الحسابات', 'users': 'المستخدمون',
        'audit_log': 'سجل التدقيق', 'settings': 'الإعدادات', 'reports': 'التقارير',
        'login': 'تسجيل الدخول', 'logout': 'تسجيل الخروج', 'exit': 'خروج',
        'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'full_name': 'الاسم الكامل',
        'role': 'الصلاحية', 'admin': 'مدير', 'user': 'مستخدم', 'viewer': 'مشاهد',
        'add': 'إضافة', 'edit': 'تعديل', 'delete': 'حذف', 'save': 'حفظ', 'cancel': 'إلغاء',
        'search': 'بحث', 'company_name': 'اسم الشركة', 'amount': 'المبلغ', 'type': 'النوع',
        'incoming': 'وارد', 'outgoing': 'صادر', 'date': 'التاريخ', 'currency': 'العملة',
        'notes': 'ملاحظات', 'net': 'صافي', 'success': 'نجاح', 'error': 'خطأ', 'warning': 'تحذير',
        'yes': 'نعم', 'no': 'لا', 'confirm_delete': 'هل أنت متأكد من الحذف؟',
        'language': 'اللغة', 'remember_user': 'تذكر المستخدم', 'show_hide_password': 'إظهار/إخفاء كلمة المرور',
        'switch_account': 'تبديل الحساب / مسح المستخدم المحفوظ', 'verifying': 'جاري التحقق...',
        'missing_login_fields': 'يرجى إدخال اسم المستخدم وكلمة المرور',
        'invalid_login': 'اسم المستخدم أو كلمة المرور غير صحيحة',
        'login_failed': 'فشل تسجيل الدخول', 'saved_user_cleared': 'تم مسح اسم المستخدم المخزن',
        'admin_default_warning': 'عند أول تشغيل: غيّر كلمة مرور admin الافتراضية فورًا.',
        'appearance': 'المظهر', 'theme': 'الثيم', 'light': 'فاتح', 'dark': 'داكن',
        'save_appearance': 'تطبيق وحفظ المظهر', 'language_settings': 'إعدادات اللغة',
        'language_restart_note': 'تُطبّق اللغة على الواجهات المركزية فوراً، وقد تحتاج بعض النوافذ المفتوحة إلى إعادة فتح.',
        'save_language': 'حفظ اللغة', 'language_saved': 'تم حفظ اللغة',
        'print_date': 'تاريخ الطباعة', 'document': 'مستند', 'report': 'تقرير', 'invoice': 'فاتورة',
        'voucher': 'سند', 'return_doc': 'مرتجع', 'no_print_content': 'لا يوجد محتوى للطباعة',
        'no_pdf_content': 'لا يوجد محتوى للحفظ', 'print_preview': 'معاينة الطباعة', 'print': 'طباعة',
        'save_pdf': 'حفظ PDF', 'company': 'الشركة', 'tax_number': 'الرقم الضريبي',
        'phone': 'هاتف', 'email': 'بريد', 'printed_at': 'تاريخ الطباعة',
        'total': 'الإجمالي', 'paid': 'المدفوع', 'remaining': 'المتبقي', 'discount': 'الخصم', 'tax': 'الضريبة',
        'barcode': 'الباركود', 'item': 'المادة', 'unit': 'الوحدة', 'quantity': 'الكمية',
        'unit_price': 'سعر الوحدة', 'line_total': 'إجمالي السطر', 'conversion_factor': 'عامل التحويل',
        'base_quantity': 'الكمية الأساسية', 'footer_thanks': 'شكراً لتعاملكم معنا',
        'sales': 'المبيعات', 'purchases': 'المشتريات', 'inventory': 'المخزون', 'manufacturing': 'التصنيع',
        'management': 'الإدارة', 'help': 'مساعدة', 'file': 'ملف', 'view': 'عرض', 'themes': 'الثيمات',
        'about': 'حول البرنامج', 'touch_mode': 'الوضع اللمسي', 'show_title_bar': 'إظهار شريط العنوان',
        'pos': 'بيع سريع POS', 'sales_invoices': 'فواتير البيع', 'purchase_invoices': 'فواتير الشراء',
        'customers': 'العملاء', 'suppliers': 'الموردون', 'receipt_vouchers': 'سندات قبض', 'payment_vouchers': 'سندات دفع',
        'sales_returns': 'مرتجعات المبيعات', 'purchase_returns': 'مرتجعات المشتريات', 'cashboxes_banks': 'الصناديق والبنوك',
        'items': 'المواد', 'categories': 'التصنيفات', 'warehouses': 'المستودعات', 'branches': 'الفروع',
        'bom': 'قوائم المواد', 'production_orders': 'أوامر الإنتاج', 'income_statement': 'قائمة الدخل',
        'balance_sheet': 'الميزانية العمومية', 'customer_statement': 'كشف حساب عميل', 'supplier_statement': 'كشف حساب مورد',
        'number': 'الرقم',
        'party': 'الطرف',
        'account': 'الحساب',
        'description': 'البيان',
        'receiver': 'المستلم',
        'cash': 'نقدي',
        'payment_method': 'طريقة الدفع',
        'subtotal': 'الإجمالي قبل الخصم',
        'no_data': 'لا توجد بيانات',
        'no_items': 'لا توجد مواد',
        'receiver_signature': 'توقيع المستلم',
        'accountant': 'المحاسب',
        'report_generated': 'تم الإنشاء بواسطة الراجحي للمحاسبة',
        'expense_voucher': 'سند مصروف',
        'column': 'عمود',
        'unsaved_changes_title': 'تغييرات غير محفوظة',
        'unsaved_changes_message': 'لديك تغييرات غير محفوظة. هل تريد الخروج دون حفظ؟',
        'openpyxl_missing': 'مكتبة openpyxl غير مثبتة',
        'table_report': 'تقرير جدول',
    },
    'en': {
        'app_title': 'Alrajhi Accounting', 'app_subtitle': 'Accounting, inventory and manufacturing system',
        'secure_login_subtitle': 'Secure system login', 'connection_mode': 'Operating mode',
        'remote_mode': 'Connected to server', 'local_mode': 'Local',
        'startup_database': 'Database', 'startup_license': 'License', 'startup_login': 'Login', 'startup_ui': 'Interface',
        'startup_init': 'Initializing startup', 'startup_loading': 'Initializing system...',
        'startup_do_not_close': 'Please do not close the application while loading',
        'startup_error_title': 'Startup could not be completed', 'startup_error_detail': 'Review the message and try again.',
        'dashboard': 'Dashboard', 'accounts': 'Accounts', 'users': 'Users', 'audit_log': 'Audit Log',
        'settings': 'Settings', 'reports': 'Reports', 'login': 'Login', 'logout': 'Logout', 'exit': 'Exit',
        'username': 'Username', 'password': 'Password', 'full_name': 'Full Name', 'role': 'Role',
        'admin': 'Admin', 'user': 'User', 'viewer': 'Viewer', 'add': 'Add', 'edit': 'Edit', 'delete': 'Delete',
        'save': 'Save', 'cancel': 'Cancel', 'search': 'Search', 'company_name': 'Company Name', 'amount': 'Amount',
        'type': 'Type', 'incoming': 'Incoming', 'outgoing': 'Outgoing', 'date': 'Date', 'currency': 'Currency',
        'notes': 'Notes', 'net': 'Net', 'success': 'Success', 'error': 'Error', 'warning': 'Warning',
        'yes': 'Yes', 'no': 'No', 'confirm_delete': 'Are you sure?', 'language': 'Language',
        'remember_user': 'Remember user', 'show_hide_password': 'Show/hide password',
        'switch_account': 'Switch account / clear saved user', 'verifying': 'Verifying...',
        'missing_login_fields': 'Please enter username and password', 'invalid_login': 'Invalid username or password',
        'login_failed': 'Login failed', 'saved_user_cleared': 'Saved username cleared',
        'admin_default_warning': 'First run: change the default admin password immediately.',
        'appearance': 'Appearance', 'theme': 'Theme', 'light': 'Light', 'dark': 'Dark',
        'save_appearance': 'Apply and save appearance', 'language_settings': 'Language settings',
        'language_restart_note': 'The language is applied to central screens immediately; some open windows may need reopening.',
        'save_language': 'Save language', 'language_saved': 'Language saved',
        'print_date': 'Print date', 'document': 'Document', 'report': 'Report', 'invoice': 'Invoice', 'voucher': 'Voucher',
        'return_doc': 'Return', 'no_print_content': 'No content to print', 'no_pdf_content': 'No content to save',
        'print_preview': 'Print preview', 'print': 'Print', 'save_pdf': 'Save PDF', 'company': 'Company',
        'tax_number': 'Tax number', 'phone': 'Phone', 'email': 'Email', 'printed_at': 'Print date',
        'total': 'Total', 'paid': 'Paid', 'remaining': 'Remaining', 'discount': 'Discount', 'tax': 'Tax',
        'barcode': 'Barcode', 'item': 'Item', 'unit': 'Unit', 'quantity': 'Quantity', 'unit_price': 'Unit price',
        'line_total': 'Line total', 'conversion_factor': 'Conversion', 'base_quantity': 'Base quantity', 'footer_thanks': 'Thank you for your business',
        'sales': 'Sales', 'purchases': 'Purchases', 'inventory': 'Inventory', 'manufacturing': 'Manufacturing',
        'management': 'Management', 'help': 'Help', 'file': 'File', 'view': 'View', 'themes': 'Themes', 'about': 'About',
        'touch_mode': 'Touch mode', 'show_title_bar': 'Show title bar', 'pos': 'Quick Sale POS',
        'sales_invoices': 'Sales invoices', 'purchase_invoices': 'Purchase invoices', 'customers': 'Customers',
        'suppliers': 'Suppliers', 'receipt_vouchers': 'Receipt vouchers', 'payment_vouchers': 'Payment vouchers',
        'sales_returns': 'Sales returns', 'purchase_returns': 'Purchase returns', 'cashboxes_banks': 'Cashboxes & Banks',
        'items': 'Items', 'categories': 'Categories', 'warehouses': 'Warehouses', 'branches': 'Branches',
        'bom': 'Bills of materials', 'production_orders': 'Production orders', 'income_statement': 'Income statement',
        'balance_sheet': 'Balance sheet', 'customer_statement': 'Customer statement', 'supplier_statement': 'Supplier statement',
        'number': 'No.',
        'party': 'Party',
        'account': 'Account',
        'description': 'Description',
        'receiver': 'Receiver',
        'cash': 'Cash',
        'payment_method': 'Payment method',
        'subtotal': 'Subtotal',
        'no_data': 'No data',
        'no_items': 'No items',
        'receiver_signature': 'Receiver signature',
        'accountant': 'Accountant',
        'report_generated': 'Generated by Alrajhi Accounting',
        'expense_voucher': 'Expense voucher',
        'column': 'Column',
        'unsaved_changes_title': 'Unsaved changes',
        'unsaved_changes_message': 'You have unsaved changes. Exit without saving?',
        'openpyxl_missing': 'openpyxl is not installed',
        'table_report': 'Table report',
    },
    'de': {
        'app_title': 'Alrajhi Buchhaltung', 'app_subtitle': 'Buchhaltung, Lager und Fertigung',
        'secure_login_subtitle': 'Sichere Anmeldung am System', 'connection_mode': 'Betriebsmodus',
        'remote_mode': 'Mit Server verbunden', 'local_mode': 'Lokal',
        'startup_database': 'Datenbank', 'startup_license': 'Lizenz', 'startup_login': 'Anmeldung', 'startup_ui': 'Oberfläche',
        'startup_init': 'Start wird vorbereitet', 'startup_loading': 'System wird initialisiert...',
        'startup_do_not_close': 'Bitte Anwendung während des Ladens nicht schließen',
        'startup_error_title': 'Start konnte nicht abgeschlossen werden', 'startup_error_detail': 'Meldung prüfen und erneut versuchen.',
        'dashboard': 'Dashboard', 'accounts': 'Konten', 'users': 'Benutzer', 'audit_log': 'Prüfprotokoll',
        'settings': 'Einstellungen', 'reports': 'Berichte', 'login': 'Anmelden', 'logout': 'Abmelden', 'exit': 'Beenden',
        'username': 'Benutzername', 'password': 'Passwort', 'full_name': 'Vollständiger Name', 'role': 'Rolle',
        'admin': 'Administrator', 'user': 'Benutzer', 'viewer': 'Betrachter', 'add': 'Hinzufügen', 'edit': 'Bearbeiten',
        'delete': 'Löschen', 'save': 'Speichern', 'cancel': 'Abbrechen', 'search': 'Suchen',
        'company_name': 'Firmenname', 'amount': 'Betrag', 'type': 'Typ', 'incoming': 'Eingang', 'outgoing': 'Ausgang',
        'date': 'Datum', 'currency': 'Währung', 'notes': 'Notizen', 'net': 'Netto', 'success': 'Erfolg',
        'error': 'Fehler', 'warning': 'Warnung', 'yes': 'Ja', 'no': 'Nein', 'confirm_delete': 'Sind Sie sicher?',
        'language': 'Sprache', 'remember_user': 'Benutzer merken', 'show_hide_password': 'Passwort anzeigen/verbergen',
        'switch_account': 'Konto wechseln / gespeicherten Benutzer löschen', 'verifying': 'Wird geprüft...',
        'missing_login_fields': 'Bitte Benutzername und Passwort eingeben', 'invalid_login': 'Benutzername oder Passwort ist falsch',
        'login_failed': 'Anmeldung fehlgeschlagen', 'saved_user_cleared': 'Gespeicherter Benutzername wurde gelöscht',
        'admin_default_warning': 'Erster Start: Standardpasswort des admin-Benutzers sofort ändern.',
        'appearance': 'Darstellung', 'theme': 'Design', 'light': 'Hell', 'dark': 'Dunkel',
        'save_appearance': 'Darstellung anwenden und speichern', 'language_settings': 'Spracheinstellungen',
        'language_restart_note': 'Die Sprache wird zentral sofort angewendet; einige geöffnete Fenster müssen ggf. neu geöffnet werden.',
        'save_language': 'Sprache speichern', 'language_saved': 'Sprache gespeichert',
        'print_date': 'Druckdatum', 'document': 'Dokument', 'report': 'Bericht', 'invoice': 'Rechnung',
        'voucher': 'Beleg', 'return_doc': 'Retoure', 'no_print_content': 'Kein Inhalt zum Drucken',
        'no_pdf_content': 'Kein Inhalt zum Speichern', 'print_preview': 'Druckvorschau', 'print': 'Drucken',
        'save_pdf': 'PDF speichern', 'company': 'Firma', 'tax_number': 'Steuernummer', 'phone': 'Telefon', 'email': 'E-Mail',
        'printed_at': 'Druckdatum', 'total': 'Gesamt', 'paid': 'Bezahlt', 'remaining': 'Restbetrag',
        'discount': 'Rabatt', 'tax': 'Steuer', 'barcode': 'Barcode', 'item': 'Artikel', 'unit': 'Einheit',
        'quantity': 'Menge', 'unit_price': 'Einzelpreis', 'line_total': 'Zeilensumme',
        'conversion_factor': 'Umrechnung', 'base_quantity': 'Basismenge', 'footer_thanks': 'Vielen Dank für Ihr Vertrauen',
        'sales': 'Verkauf', 'purchases': 'Einkauf', 'inventory': 'Lager', 'manufacturing': 'Fertigung',
        'management': 'Verwaltung', 'help': 'Hilfe', 'file': 'Datei', 'view': 'Ansicht', 'themes': 'Designs', 'about': 'Über das Programm',
        'touch_mode': 'Touch-Modus', 'show_title_bar': 'Titelleiste anzeigen', 'pos': 'Schnellverkauf POS',
        'sales_invoices': 'Verkaufsrechnungen', 'purchase_invoices': 'Einkaufsrechnungen', 'customers': 'Kunden',
        'suppliers': 'Lieferanten', 'receipt_vouchers': 'Zahlungseingänge', 'payment_vouchers': 'Zahlungsausgänge',
        'sales_returns': 'Verkaufsretouren', 'purchase_returns': 'Einkaufsretouren', 'cashboxes_banks': 'Kassen & Banken',
        'items': 'Artikel', 'categories': 'Kategorien', 'warehouses': 'Lager', 'branches': 'Filialen',
        'bom': 'Stücklisten', 'production_orders': 'Produktionsaufträge', 'income_statement': 'GuV-Rechnung',
        'balance_sheet': 'Bilanz', 'customer_statement': 'Kundenkontoauszug', 'supplier_statement': 'Lieferantenkontoauszug',
        'number': 'Nr.',
        'party': 'Partei',
        'account': 'Konto',
        'description': 'Beschreibung',
        'receiver': 'Empfänger',
        'cash': 'Bar',
        'payment_method': 'Zahlungsart',
        'subtotal': 'Zwischensumme',
        'no_data': 'Keine Daten',
        'no_items': 'Keine Artikel',
        'receiver_signature': 'Unterschrift Empfänger',
        'accountant': 'Buchhalter',
        'report_generated': 'Erstellt mit Alrajhi Buchhaltung',
        'expense_voucher': 'Ausgabenbeleg',
        'column': 'Spalte',
        'unsaved_changes_title': 'Ungespeicherte Änderungen',
        'unsaved_changes_message': 'Sie haben ungespeicherte Änderungen. Ohne Speichern schließen?',
        'openpyxl_missing': 'openpyxl ist nicht installiert',
        'table_report': 'Tabellenbericht',
    },
}



# Extra key-based labels for extended UI and print templates.
_translations['ar'].update({
    'number':'الرقم','party':'الطرف','account':'الحساب','description':'البيان','receiver':'المستلم','cash':'نقدي',
    'payment_method':'طريقة الدفع','subtotal':'الإجمالي قبل الخصم','no_data':'لا توجد بيانات','no_items':'لا توجد مواد',
    'receiver_signature':'توقيع المستلم','accountant':'المحاسب','report_generated':'تم الإنشاء بواسطة الراجحي للمحاسبة',
    'expense_voucher':'سند مصروف','column':'عمود','table_report':'تقرير جدول','print_templates':'قوالب الطباعة',
    'print_template_language':'لغة قالب الطباعة','auto_by_language':'تلقائي حسب اللغة','template_a4':'قالب A4','template_thermal':'قالب حراري',
})
_translations['en'].update({
    'number':'No.','party':'Party','account':'Account','description':'Description','receiver':'Receiver','cash':'Cash',
    'payment_method':'Payment method','subtotal':'Subtotal','no_data':'No data','no_items':'No items',
    'receiver_signature':'Receiver signature','accountant':'Accountant','report_generated':'Generated by Alrajhi Accounting',
    'expense_voucher':'Expense voucher','column':'Column','table_report':'Table report','print_templates':'Print templates',
    'print_template_language':'Print template language','auto_by_language':'Automatic by language','template_a4':'A4 template','template_thermal':'Thermal template',
})
_translations['de'].update({
    'number':'Nr.','party':'Partei','account':'Konto','description':'Beschreibung','receiver':'Empfänger','cash':'Bar',
    'payment_method':'Zahlungsart','subtotal':'Zwischensumme','no_data':'Keine Daten','no_items':'Keine Artikel',
    'receiver_signature':'Unterschrift Empfänger','accountant':'Buchhalter','report_generated':'Erstellt mit Alrajhi Buchhaltung',
    'expense_voucher':'Ausgabenbeleg','column':'Spalte','table_report':'Tabellenbericht','print_templates':'Druckvorlagen',
    'print_template_language':'Sprache der Druckvorlage','auto_by_language':'Automatisch nach Sprache','template_a4':'A4-Vorlage','template_thermal':'Thermovorlage',
})

# French was visible in older login UI; keep it as an alias to English until a full FR pack is supplied.
_translations['fr'] = dict(_translations['en'])
LANGUAGES['fr'] = {'native_name': 'Français', 'direction': 'ltr', 'html_lang': 'fr'}



# Direct visible-text translations used by legacy UI strings, table headers and print labels.
# Keys are normalized Arabic/English labels as they appear in older widgets.
_TEXT_ALIASES = {
    'ar': {
        'بحث...': 'بحث...', 'السابق': 'السابق', 'التالي': 'التالي', 'إضافة': 'إضافة', 'تعديل': 'تعديل', 'حذف': 'حذف',
        'طباعة': 'طباعة', 'تصدير إلى Excel': 'تصدير إلى Excel', 'نسخ': 'نسخ', 'الأعمدة': 'الأعمدة',
        'إعادة ضبط الأعمدة': 'إعادة ضبط الأعمدة', 'حفظ التقرير': 'حفظ التقرير', 'تقرير': 'تقرير',
        'تعذر الطباعة': 'تعذر الطباعة', 'تنبيه': 'تنبيه', 'نجاح': 'نجاح', 'تم التصدير إلى': 'تم التصدير إلى',
        'رقم': 'رقم', 'الرقم': 'الرقم', 'الاسم': 'الاسم', 'الاسم الكامل': 'الاسم الكامل', 'الهاتف': 'الهاتف',
        'العنوان': 'العنوان', 'البريد الإلكتروني': 'البريد الإلكتروني', 'الرصيد': 'الرصيد', 'الحالة': 'الحالة',
        'ملاحظات': 'ملاحظات', 'التاريخ': 'التاريخ', 'النوع': 'النوع', 'المبلغ': 'المبلغ', 'البيان': 'البيان',
        'الطرف': 'الطرف', 'الحساب': 'الحساب', 'المستخدم': 'المستخدم', 'المستلم': 'المستلم', 'المحاسب': 'المحاسب',
        'العميل': 'العميل', 'المورد': 'المورد', 'المادة': 'المادة', 'المواد': 'المواد', 'التصنيف': 'التصنيف',
        'الباركود': 'الباركود', 'الوحدة': 'الوحدة', 'الكمية': 'الكمية', 'السعر': 'السعر', 'سعر الوحدة': 'سعر الوحدة',
        'سعر الشراء': 'سعر الشراء', 'سعر البيع': 'سعر البيع', 'الخصم': 'الخصم', 'الضريبة': 'الضريبة',
        'الإجمالي': 'الإجمالي', 'إجمالي السطر': 'إجمالي السطر', 'المدفوع': 'المدفوع', 'المتبقي': 'المتبقي',
        'الصافي': 'الصافي', 'المستودع': 'المستودع', 'المستودعات': 'المستودعات', 'الفرع': 'الفرع', 'الفروع': 'الفروع',
        'الصندوق': 'الصندوق', 'البنك': 'البنك', 'الصناديق والبنوك': 'الصناديق والبنوك', 'طريقة الدفع': 'طريقة الدفع',
        'نقدي': 'نقدي', 'آجل': 'آجل', 'تحويل بنكي': 'تحويل بنكي', 'بطاقة': 'بطاقة',
        'فاتورة بيع': 'فاتورة بيع', 'فاتورة شراء': 'فاتورة شراء', 'فواتير البيع': 'فواتير البيع', 'فواتير الشراء': 'فواتير الشراء',
        'مرتجعات المبيعات': 'مرتجعات المبيعات', 'مرتجعات المشتريات': 'مرتجعات المشتريات', 'سند قبض': 'سند قبض', 'سند دفع': 'سند دفع',
        'سندات قبض': 'سندات قبض', 'سندات دفع': 'سندات دفع', 'لوحة التحكم': 'لوحة التحكم', 'التقارير': 'التقارير',
        'الإعدادات': 'الإعدادات', 'سجل التدقيق': 'سجل التدقيق', 'المستخدمون': 'المستخدمون', 'العملاء': 'العملاء',
        'الموردون': 'الموردون', 'التصنيفات': 'التصنيفات', 'التصنيع': 'التصنيع', 'أوامر الإنتاج': 'أوامر الإنتاج',
        'قوائم المواد': 'قوائم المواد', 'تاريخ الطباعة': 'تاريخ الطباعة', 'عدد السجلات': 'عدد السجلات',
        'لا يوجد محتوى للطباعة': 'لا يوجد محتوى للطباعة', 'لا توجد بيانات': 'لا توجد بيانات',
        'الإجمالي قبل الخصم': 'الإجمالي قبل الخصم', 'الإجمالي النهائي': 'الإجمالي النهائي',
        'عامل التحويل': 'عامل التحويل', 'الكمية الأساسية': 'الكمية الأساسية', 'توقيع المستلم': 'توقيع المستلم',
        'البيانات الأساسية': 'البيانات الأساسية', 'الأسعار': 'الأسعار', 'المخزون': 'المخزون', 'الوحدات الفرعية': 'الوحدات الفرعية',
        'جديد': 'جديد', 'حفظ': 'حفظ', 'إلغاء': 'إلغاء', 'تحديث': 'تحديث', 'بحث': 'بحث', 'عرض': 'عرض',
        'من أصل': 'من أصل', 'سجل': 'سجل', 'الصفحة': 'الصفحة', 'من': 'من', 'إلى': 'إلى',
        'number': 'الرقم',
        'party': 'الطرف',
        'account': 'الحساب',
        'description': 'البيان',
        'receiver': 'المستلم',
        'cash': 'نقدي',
        'payment_method': 'طريقة الدفع',
        'subtotal': 'الإجمالي قبل الخصم',
        'no_data': 'لا توجد بيانات',
        'no_items': 'لا توجد مواد',
        'receiver_signature': 'توقيع المستلم',
        'accountant': 'المحاسب',
        'report_generated': 'تم الإنشاء بواسطة الراجحي للمحاسبة',
        'expense_voucher': 'سند مصروف',
        'column': 'عمود',
        'unsaved_changes_title': 'تغييرات غير محفوظة',
        'unsaved_changes_message': 'لديك تغييرات غير محفوظة. هل تريد الخروج دون حفظ؟',
        'openpyxl_missing': 'مكتبة openpyxl غير مثبتة',
        'table_report': 'تقرير جدول',
    },
    'en': {
        'بحث...': 'Search...', 'السابق': 'Previous', 'التالي': 'Next', 'إضافة': 'Add', 'تعديل': 'Edit', 'حذف': 'Delete',
        'طباعة': 'Print', 'تصدير إلى Excel': 'Export to Excel', 'نسخ': 'Copy', 'الأعمدة': 'Columns',
        'إعادة ضبط الأعمدة': 'Reset columns', 'حفظ التقرير': 'Save report', 'تقرير': 'Report',
        'تعذر الطباعة': 'Printing failed', 'تنبيه': 'Warning', 'نجاح': 'Success', 'تم التصدير إلى': 'Exported to',
        'رقم': 'No.', 'الرقم': 'No.', 'الاسم': 'Name', 'الاسم الكامل': 'Full name', 'الهاتف': 'Phone',
        'العنوان': 'Address', 'البريد الإلكتروني': 'Email', 'الرصيد': 'Balance', 'الحالة': 'Status',
        'ملاحظات': 'Notes', 'التاريخ': 'Date', 'النوع': 'Type', 'المبلغ': 'Amount', 'البيان': 'Description',
        'الطرف': 'Party', 'الحساب': 'Account', 'المستخدم': 'User', 'المستلم': 'Receiver', 'المحاسب': 'Accountant',
        'العميل': 'Customer', 'المورد': 'Supplier', 'المادة': 'Item', 'المواد': 'Items', 'التصنيف': 'Category',
        'الباركود': 'Barcode', 'الوحدة': 'Unit', 'الكمية': 'Quantity', 'السعر': 'Price', 'سعر الوحدة': 'Unit price',
        'سعر الشراء': 'Purchase price', 'سعر البيع': 'Sale price', 'الخصم': 'Discount', 'الضريبة': 'Tax',
        'الإجمالي': 'Total', 'إجمالي السطر': 'Line total', 'المدفوع': 'Paid', 'المتبقي': 'Remaining',
        'الصافي': 'Net', 'المستودع': 'Warehouse', 'المستودعات': 'Warehouses', 'الفرع': 'Branch', 'الفروع': 'Branches',
        'الصندوق': 'Cashbox', 'البنك': 'Bank', 'الصناديق والبنوك': 'Cashboxes & Banks', 'طريقة الدفع': 'Payment method',
        'نقدي': 'Cash', 'آجل': 'Credit', 'تحويل بنكي': 'Bank transfer', 'بطاقة': 'Card',
        'فاتورة بيع': 'Sales invoice', 'فاتورة شراء': 'Purchase invoice', 'فواتير البيع': 'Sales invoices', 'فواتير الشراء': 'Purchase invoices',
        'مرتجعات المبيعات': 'Sales returns', 'مرتجعات المشتريات': 'Purchase returns', 'سند قبض': 'Receipt voucher', 'سند دفع': 'Payment voucher',
        'سندات قبض': 'Receipt vouchers', 'سندات دفع': 'Payment vouchers', 'لوحة التحكم': 'Dashboard', 'التقارير': 'Reports',
        'الإعدادات': 'Settings', 'سجل التدقيق': 'Audit log', 'المستخدمون': 'Users', 'العملاء': 'Customers',
        'الموردون': 'Suppliers', 'التصنيفات': 'Categories', 'التصنيع': 'Manufacturing', 'أوامر الإنتاج': 'Production orders',
        'قوائم المواد': 'Bills of materials', 'تاريخ الطباعة': 'Print date', 'عدد السجلات': 'Record count',
        'لا يوجد محتوى للطباعة': 'No content to print', 'لا توجد بيانات': 'No data',
        'الإجمالي قبل الخصم': 'Subtotal', 'الإجمالي النهائي': 'Final total',
        'عامل التحويل': 'Conversion factor', 'الكمية الأساسية': 'Base quantity', 'توقيع المستلم': 'Receiver signature',
        'البيانات الأساسية': 'Basic data', 'الأسعار': 'Prices', 'المخزون': 'Inventory', 'الوحدات الفرعية': 'Sub-units',
        'جديد': 'New', 'حفظ': 'Save', 'إلغاء': 'Cancel', 'تحديث': 'Refresh', 'بحث': 'Search', 'عرض': 'Showing',
        'من أصل': 'of', 'سجل': 'record', 'الصفحة': 'Page', 'من': 'from', 'إلى': 'to',
        'number': 'No.',
        'party': 'Party',
        'account': 'Account',
        'description': 'Description',
        'receiver': 'Receiver',
        'cash': 'Cash',
        'payment_method': 'Payment method',
        'subtotal': 'Subtotal',
        'no_data': 'No data',
        'no_items': 'No items',
        'receiver_signature': 'Receiver signature',
        'accountant': 'Accountant',
        'report_generated': 'Generated by Alrajhi Accounting',
        'expense_voucher': 'Expense voucher',
        'column': 'Column',
        'unsaved_changes_title': 'Unsaved changes',
        'unsaved_changes_message': 'You have unsaved changes. Exit without saving?',
        'openpyxl_missing': 'openpyxl is not installed',
        'table_report': 'Table report',
    },
    'de': {
        'بحث...': 'Suchen...', 'السابق': 'Zurück', 'التالي': 'Weiter', 'إضافة': 'Hinzufügen', 'تعديل': 'Bearbeiten', 'حذف': 'Löschen',
        'طباعة': 'Drucken', 'تصدير إلى Excel': 'Nach Excel exportieren', 'نسخ': 'Kopieren', 'الأعمدة': 'Spalten',
        'إعادة ضبط الأعمدة': 'Spalten zurücksetzen', 'حفظ التقرير': 'Bericht speichern', 'تقرير': 'Bericht',
        'تعذر الطباعة': 'Drucken fehlgeschlagen', 'تنبيه': 'Warnung', 'نجاح': 'Erfolg', 'تم التصدير إلى': 'Exportiert nach',
        'رقم': 'Nr.', 'الرقم': 'Nr.', 'الاسم': 'Name', 'الاسم الكامل': 'Vollständiger Name', 'الهاتف': 'Telefon',
        'العنوان': 'Adresse', 'البريد الإلكتروني': 'E-Mail', 'الرصيد': 'Saldo', 'الحالة': 'Status',
        'ملاحظات': 'Notizen', 'التاريخ': 'Datum', 'النوع': 'Typ', 'المبلغ': 'Betrag', 'البيان': 'Beschreibung',
        'الطرف': 'Partei', 'الحساب': 'Konto', 'المستخدم': 'Benutzer', 'المستلم': 'Empfänger', 'المحاسب': 'Buchhalter',
        'العميل': 'Kunde', 'المورد': 'Lieferant', 'المادة': 'Artikel', 'المواد': 'Artikel', 'التصنيف': 'Kategorie',
        'الباركود': 'Barcode', 'الوحدة': 'Einheit', 'الكمية': 'Menge', 'السعر': 'Preis', 'سعر الوحدة': 'Einzelpreis',
        'سعر الشراء': 'Einkaufspreis', 'سعر البيع': 'Verkaufspreis', 'الخصم': 'Rabatt', 'الضريبة': 'Steuer',
        'الإجمالي': 'Gesamt', 'إجمالي السطر': 'Zeilensumme', 'المدفوع': 'Bezahlt', 'المتبقي': 'Restbetrag',
        'الصافي': 'Netto', 'المستودع': 'Lager', 'المستودعات': 'Lager', 'الفرع': 'Filiale', 'الفروع': 'Filialen',
        'الصندوق': 'Kasse', 'البنك': 'Bank', 'الصناديق والبنوك': 'Kassen & Banken', 'طريقة الدفع': 'Zahlungsart',
        'نقدي': 'Bar', 'آجل': 'Auf Kredit', 'تحويل بنكي': 'Banküberweisung', 'بطاقة': 'Karte',
        'فاتورة بيع': 'Verkaufsrechnung', 'فاتورة شراء': 'Einkaufsrechnung', 'فواتير البيع': 'Verkaufsrechnungen', 'فواتير الشراء': 'Einkaufsrechnungen',
        'مرتجعات المبيعات': 'Verkaufsretouren', 'مرتجعات المشتريات': 'Einkaufsretouren', 'سند قبض': 'Zahlungseingang', 'سند دفع': 'Zahlungsausgang',
        'سندات قبض': 'Zahlungseingänge', 'سندات دفع': 'Zahlungsausgänge', 'لوحة التحكم': 'Dashboard', 'التقارير': 'Berichte',
        'الإعدادات': 'Einstellungen', 'سجل التدقيق': 'Prüfprotokoll', 'المستخدمون': 'Benutzer', 'العملاء': 'Kunden',
        'الموردون': 'Lieferanten', 'التصنيفات': 'Kategorien', 'التصنيع': 'Fertigung', 'أوامر الإنتاج': 'Produktionsaufträge',
        'قوائم المواد': 'Stücklisten', 'تاريخ الطباعة': 'Druckdatum', 'عدد السجلات': 'Anzahl Datensätze',
        'لا يوجد محتوى للطباعة': 'Kein Inhalt zum Drucken', 'لا توجد بيانات': 'Keine Daten',
        'الإجمالي قبل الخصم': 'Zwischensumme', 'الإجمالي النهائي': 'Endsumme',
        'عامل التحويل': 'Umrechnungsfaktor', 'الكمية الأساسية': 'Basismenge', 'توقيع المستلم': 'Unterschrift Empfänger',
        'البيانات الأساسية': 'Stammdaten', 'الأسعار': 'Preise', 'المخزون': 'Lagerbestand', 'الوحدات الفرعية': 'Untereinheiten',
        'جديد': 'Neu', 'حفظ': 'Speichern', 'إلغاء': 'Abbrechen', 'تحديث': 'Aktualisieren', 'بحث': 'Suchen', 'عرض': 'Anzeige',
        'من أصل': 'von', 'سجل': 'Datensatz', 'الصفحة': 'Seite', 'من': 'von', 'إلى': 'bis'
    }
}

# English source labels used by new print/table code.
for _lang, _pairs in {
    'ar': {'No data':'لا توجد بيانات','Cash':'نقدي','Receiver signature':'توقيع المستلم','Accountant':'المحاسب','Expense voucher':'سند مصروف','Generated by Alrajhi Accounting':'تم الإنشاء بواسطة الراجحي للمحاسبة'},
    'en': {'No data':'No data','Cash':'Cash','Receiver signature':'Receiver signature','Accountant':'Accountant','Expense voucher':'Expense voucher','Generated by Alrajhi Accounting':'Generated by Alrajhi Accounting'},
    'de': {'No data':'Keine Daten','Cash':'Bar','Receiver signature':'Unterschrift Empfänger','Accountant':'Buchhalter','Expense voucher':'Ausgabenbeleg','Generated by Alrajhi Accounting':'Erstellt mit Alrajhi Buchhaltung'},
}.items():
    _TEXT_ALIASES.setdefault(_lang, {}).update(_pairs)


def _clean_visible_text(text: str) -> str:
    import re
    value = str(text or '').strip()
    value = re.sub(r'^[\W_\d\U0001F300-\U0001FAFF\u2600-\u27BF]+', '', value).strip()
    value = value.replace(':', '').strip()
    return value


def translate_text(text: str, default: str = None) -> str:
    """Translate an already-visible UI/print label.

    This complements key-based translate(). It keeps legacy widgets useful until
    every literal is converted to translation keys.
    """
    if text is None:
        return ''
    raw = str(text)
    if not raw.strip():
        return raw
    clean = _clean_visible_text(raw)
    # Exact visible label mapping first.
    value = (_TEXT_ALIASES.get(_current_lang, {}).get(clean)
             or _TEXT_ALIASES.get(_current_lang, {}).get(raw.strip()))
    if value:
        # Preserve trailing colon if present.
        if raw.strip().endswith(':') and not value.endswith(':'):
            value += ':'
        return value
    # Then use key-based map if the text happens to match a key.
    key = clean.lower().replace(' ', '_').replace('-', '_')
    return translate(key, default if default is not None else raw)


@contextmanager
def use_language(lang: str):
    old = get_language()
    try:
        if lang and lang != 'auto':
            set_language(lang)
        yield
    finally:
        set_language(old)


def load_translations():
    return _translations


def available_languages() -> Dict[str, str]:
    return {code: meta['native_name'] for code, meta in LANGUAGES.items()}


def set_language(lang: str):
    global _current_lang
    _current_lang = lang if lang in _translations else 'ar'


def get_language() -> str:
    return _current_lang


def is_rtl(lang: str = None) -> bool:
    return LANGUAGES.get(lang or _current_lang, {}).get('direction') == 'rtl'


def direction(lang: str = None) -> str:
    return 'rtl' if is_rtl(lang) else 'ltr'


def html_lang(lang: str = None) -> str:
    return LANGUAGES.get(lang or _current_lang, {}).get('html_lang', lang or _current_lang)


def translate(key: str, default: str = None) -> str:
    if key is None:
        return ''
    key = str(key)
    return (_translations.get(_current_lang, {}).get(key)
            or _translations.get('ar', {}).get(key)
            or _translations.get('en', {}).get(key)
            or default
            or key)

# Common short alias for new code.
t = translate
