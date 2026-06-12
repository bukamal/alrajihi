# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QLabel, QMessageBox, QTabWidget, QFileDialog,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings

from core.services.settings_service import settings_service
from core.services.backup_service import backup_service
from core.services.audit_service import audit_service
from currency import currency
from auth.activation import activate_network, check_network_activation
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from utils import show_toast
from core.server_control import get_server_port, server_status, start_server_process, stop_server_process, health_check, normalize_server_url, server_diagnostics
import requests
import os
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog


class SettingsWidget(QWidget):
    currency_settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.settings = settings_service
        self.setObjectName('settingsWidget')

        main = QVBoxLayout(self)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(14)
        main.addWidget(self._create_header())

        self.tabs = QTabWidget()
        self.tabs.setObjectName('settingsTabs')
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.create_appearance_tab(), '🎨 المظهر')
        self.tabs.addTab(self.create_company_tab(), '🏢 الشركة')
        self.tabs.addTab(self.create_printing_tab(), '🖨️ الطباعة')
        self.tabs.addTab(self.create_pos_tab(), '🧾 نقطة البيع')
        self.tabs.addTab(self.create_currency_tab(), '💰 العملات')
        self.tabs.addTab(self.create_rates_tab(), '💱 أسعار الصرف')
        self.tabs.addTab(self.create_network_tab(), '🌐 الشبكة')
        self.tabs.addTab(self.create_backup_tab(), '💾 النسخ والبيانات')
        main.addWidget(self.tabs, 1)

        self._apply_local_style()
        apply_modern_widget(self, '⚙️ الإعدادات', 'إعدادات النظام والطباعة والنسخ الاحتياطي والشبكة')
        self.load_rates_table()

    def _create_header(self):
        frame = QFrame()
        frame.setObjectName('settingsHeader')
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        texts = QVBoxLayout()
        title = QLabel('الإعدادات')
        title.setObjectName('settingsTitle')
        subtitle = QLabel('إدارة المظهر، الشركة، الطباعة، العملات، الشبكة، والنسخ الاحتياطي من مكان واحد.')
        subtitle.setObjectName('settingsSubtitle')
        subtitle.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(subtitle)
        layout.addLayout(texts, 1)
        self.settings_status = DesignSystem.status_pill('جاهز', 'success')
        layout.addWidget(self.settings_status, 0, Qt.AlignVCenter)
        return frame

    def _scroll_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 18)
        layout.setSpacing(14)
        scroll.setWidget(container)
        return scroll, layout

    def _card(self, title, subtitle=None):
        group = QGroupBox(title)
        group.setObjectName('settingsCard')
        box = QVBoxLayout(group)
        box.setContentsMargins(16, 18, 16, 16)
        box.setSpacing(10)
        if subtitle:
            desc = QLabel(subtitle)
            desc.setObjectName('settingsHelp')
            desc.setWordWrap(True)
            box.addWidget(desc)
        return group, box

    def _form_card(self, title, subtitle=None):
        group, box = self._card(title, subtitle)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        box.addLayout(form)
        return group, form

    def _button_row(self, *buttons):
        row = QHBoxLayout()
        row.addStretch()
        for btn in buttons:
            btn.setMinimumHeight(38)
            row.addWidget(btn)
        return row

    def _note(self, text, tone='info'):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setObjectName(f'note_{tone}')
        return lbl

    def _apply_local_style(self):
        self.setStyleSheet(self.styleSheet() + '''
            QFrame#settingsHeader { background-color: rgba(99,102,241,0.10); border: 1px solid rgba(99,102,241,0.20); border-radius: 16px; }
            QLabel#settingsTitle { font-size: 24px; font-weight: 800; }
            QLabel#settingsSubtitle, QLabel#settingsHelp { color: #64748b; font-size: 12px; }
            QTabWidget#settingsTabs::pane { border: 1px solid #e2e8f0; border-radius: 14px; background: rgba(255,255,255,0.72); }
            QTabBar::tab { min-height: 34px; padding: 8px 14px; margin: 2px; border-radius: 10px; }
            QTabBar::tab:selected { background: #4f46e5; color: white; font-weight: bold; }
            QGroupBox#settingsCard { border: 1px solid #e2e8f0; border-radius: 14px; margin-top: 12px; padding-top: 12px; background: rgba(255,255,255,0.90); font-weight: bold; }
            QGroupBox#settingsCard::title { subcontrol-origin: margin; right: 14px; padding: 0 8px; }
            QLabel#note_warning { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.35); color: #92400e; border-radius: 10px; padding: 10px; }
            QLabel#note_info { background: rgba(59,130,246,0.10); border: 1px solid rgba(59,130,246,0.30); color: #1d4ed8; border-radius: 10px; padding: 10px; }
        ''')

    def create_appearance_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات المظهر', 'تغيير شكل التطبيق وحفظه للتشغيل القادم.')
        self.theme_combo = QComboBox()
        self.theme_combo.addItem('فاتح', 'light')
        self.theme_combo.addItem('داكن', 'dark')
        current_theme = settings_service.get_theme()
        self.theme_combo.setCurrentIndex(1 if current_theme == 'dark' else 0)
        form.addRow('الثيم:', self.theme_combo)
        form.addRow(self._note('سيتم تطبيق الثيم فورًا على النافذة الحالية، ويُحفظ تلقائيًا للمرة القادمة.', 'info'))
        apply_btn = QPushButton('تطبيق وحفظ المظهر')
        apply_btn.setObjectName('primary')
        apply_btn.clicked.connect(self.save_appearance_settings)
        form.addRow(self._button_row(apply_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll


    def create_pos_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات نقطة البيع', 'الورديات اختيارية. عند تعطيلها يسجل POS البيع مباشرة على الصندوق الافتراضي دون فتح أو إغلاق وردية.')
        self.pos_use_shifts_check = QCheckBox('تفعيل ورديات الكاشير في POS')
        self.pos_use_shifts_check.setChecked(settings_service.pos_shifts_enabled())
        form.addRow('', self.pos_use_shifts_check)
        form.addRow(self._note('افتراضيًا الورديات معطلة. لا تُحذف بيانات الورديات القديمة، وتبقى للتقارير والأرشفة.', 'info'))
        save_btn = QPushButton('حفظ إعدادات نقطة البيع')
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_pos_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll

    def save_pos_settings(self):
        try:
            settings_service.save_pos_settings(self.pos_use_shifts_check.isChecked())
            show_toast('تم حفظ إعدادات نقطة البيع', 'success', self)
        except Exception as e:
            QMessageBox.warning(self, 'خطأ', str(e))

    def create_company_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('معلومات الشركة', 'تظهر هذه البيانات في الفواتير والسندات والتقارير المطبوعة.')
        from config import get_company_info
        info = get_company_info()
        self.company_name_edit = QLineEdit(info.get('name', ''))
        form.addRow('اسم الشركة:', self.company_name_edit)
        self.company_address_edit = QLineEdit(info.get('address', ''))
        form.addRow('العنوان:', self.company_address_edit)
        self.company_phone_edit = QLineEdit(info.get('phone', ''))
        form.addRow('الهاتف:', self.company_phone_edit)
        self.company_email_edit = QLineEdit(info.get('email', ''))
        form.addRow('البريد الإلكتروني:', self.company_email_edit)
        self.company_tax_number_edit = QLineEdit(info.get('tax_number', ''))
        form.addRow('الرقم الضريبي:', self.company_tax_number_edit)
        self.company_logo_path_edit = QLineEdit(info.get('logo_path', ''))
        logo_btn = QPushButton('اختيار شعار')
        logo_btn.clicked.connect(self.browse_logo)
        logo_row = QHBoxLayout()
        logo_row.addWidget(self.company_logo_path_edit, 1)
        logo_row.addWidget(logo_btn)
        form.addRow('شعار الشركة:', logo_row)
        save_company_btn = QPushButton('حفظ معلومات الشركة')
        save_company_btn.setObjectName('primary')
        save_company_btn.clicked.connect(self.save_company_info)
        form.addRow(self._button_row(save_company_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll

    def create_printing_tab(self):
        scroll, layout = self._scroll_tab()
        cfg = settings_service.get_printing_settings()

        templates_group, form = self._form_card('قوالب HTML الموحدة', 'هذه الإعدادات تغذي قالب HTML واحد للفواتير، السندات، المرتجعات، الجداول، التقارير وملفات PDF.')
        self.print_invoice_template = QComboBox()
        self.print_invoice_template.addItem('A4 احترافي', 'a4')
        self.print_invoice_template.addItem('حراري 80mm', 'thermal80')
        self.print_invoice_template.addItem('حراري 58mm', 'thermal58')
        idx = self.print_invoice_template.findData(cfg.get('invoice_template', 'a4'))
        self.print_invoice_template.setCurrentIndex(max(0, idx))
        form.addRow('قالب الفاتورة:', self.print_invoice_template)

        self.print_report_template = QComboBox()
        self.print_report_template.addItem('A4 احترافي', 'a4')
        self.print_report_template.addItem('حراري 80mm', 'thermal80')
        self.print_report_template.addItem('حراري 58mm', 'thermal58')
        idx = self.print_report_template.findData(cfg.get('report_template', 'a4'))
        self.print_report_template.setCurrentIndex(max(0, idx))
        form.addRow('قالب التقارير والجداول:', self.print_report_template)

        self.print_voucher_template = QComboBox()
        self.print_voucher_template.addItem('A4 احترافي', 'a4')
        self.print_voucher_template.addItem('حراري 80mm', 'thermal80')
        self.print_voucher_template.addItem('حراري 58mm', 'thermal58')
        idx = self.print_voucher_template.findData(cfg.get('voucher_template', 'a4'))
        self.print_voucher_template.setCurrentIndex(max(0, idx))
        form.addRow('قالب السندات:', self.print_voucher_template)

        self.print_return_template = QComboBox()
        self.print_return_template.addItem('A4 احترافي', 'a4')
        self.print_return_template.addItem('حراري 80mm', 'thermal80')
        self.print_return_template.addItem('حراري 58mm', 'thermal58')
        idx = self.print_return_template.findData(cfg.get('return_template', cfg.get('invoice_template', 'a4')))
        self.print_return_template.setCurrentIndex(max(0, idx))
        form.addRow('قالب المرتجعات:', self.print_return_template)

        self.print_thermal_size = QComboBox()
        self.print_thermal_size.addItems(['80mm', '58mm'])
        self.print_thermal_size.setCurrentText(cfg.get('thermal_size', '80mm'))
        form.addRow('حجم الطابعة الحرارية الافتراضي:', self.print_thermal_size)
        layout.addWidget(templates_group)

        identity_group, identity_form = self._form_card('هوية الطباعة', 'ضبط الرأس، الألوان، الخط، الشعار، QR والتذييل لكل مستند مطبوع أو محفوظ كـ PDF.')
        self.print_show_logo = QCheckBox('إظهار شعار الشركة في رأس المستند')
        self.print_show_logo.setChecked(bool(cfg.get('show_logo', True)))
        identity_form.addRow(self.print_show_logo)

        self.print_show_tax = QCheckBox('إظهار الرقم الضريبي')
        self.print_show_tax.setChecked(bool(cfg.get('show_tax_number', True)))
        identity_form.addRow(self.print_show_tax)

        self.print_show_qr = QCheckBox('إظهار QR في الفواتير والمرتجعات')
        self.print_show_qr.setChecked(bool(cfg.get('show_qr', True)))
        identity_form.addRow(self.print_show_qr)

        self.print_accent_color = QLineEdit(cfg.get('accent_color', '#1d4ed8'))
        self.print_accent_color.setPlaceholderText('#1d4ed8')
        identity_form.addRow('لون العنوان والجداول:', self.print_accent_color)

        self.print_font_family = QLineEdit(cfg.get('font_family', 'Tajawal, Arial, DejaVu Sans, sans-serif'))
        identity_form.addRow('خط الطباعة:', self.print_font_family)

        self.print_font_size = QComboBox()
        self.print_font_size.addItems(['9.5pt', '10pt', '10.5pt', '11pt', '12pt'])
        self.print_font_size.setCurrentText(cfg.get('print_font_size', '10.5pt'))
        identity_form.addRow('حجم خط A4:', self.print_font_size)

        self.print_zebra_rows = QCheckBox('تظليل الصفوف بالتناوب في الجداول')
        self.print_zebra_rows.setChecked(bool(cfg.get('zebra_rows', True)))
        identity_form.addRow(self.print_zebra_rows)

        self.print_compact_tables = QCheckBox('جداول مضغوطة للكميات الكبيرة')
        self.print_compact_tables.setChecked(bool(cfg.get('compact_tables', False)))
        identity_form.addRow(self.print_compact_tables)

        self.print_footer = QLineEdit(cfg.get('footer_text', ''))
        self.print_footer.setPlaceholderText('مثال: شكراً لتعاملكم معنا')
        identity_form.addRow('تذييل المستندات:', self.print_footer)
        layout.addWidget(identity_group)

        actions_group, actions_box = self._card('الحفظ والتطبيق', 'بعد الحفظ ستستخدم جميع مسارات الطباعة القالب HTML الموحد تلقائياً: Preview، Direct Print، PDF.')
        save_btn = QPushButton('حفظ إعدادات الطباعة الموحدة')
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_printing_settings)
        actions_box.addLayout(self._button_row(save_btn))
        layout.addWidget(actions_group)
        layout.addStretch()
        return scroll

    def create_currency_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات العملات', 'اختيار العملة الأساسية والمعروضة وطريقة عرض الأرقام في الواجهة والتقارير.')
        self.base_curr = QComboBox(); self.base_curr.addItems(['USD', 'SAR', 'SYP', 'EUR', 'GBP', 'AED', 'QAR', 'KWD', 'OMR']); self.base_curr.setCurrentText(currency.get_base_currency())
        form.addRow('العملة الأساسية:', self.base_curr)
        self.display_curr = QComboBox(); self.display_curr.addItems(['USD', 'SAR', 'SYP', 'EUR', 'GBP', 'AED', 'QAR', 'KWD', 'OMR']); self.display_curr.setCurrentText(currency.get_display_currency())
        form.addRow('العملة المعروضة:', self.display_curr)
        self.decimals = QSpinBox(); self.decimals.setRange(0, 2); self.decimals.setValue(currency.get_currency_decimals())
        form.addRow('الخانات العشرية:', self.decimals)
        self.format_combo = QComboBox(); self.format_combo.addItems(['غربية', 'شرقية'])
        current = self.settings.get('number_format', 'western')
        self.format_combo.setCurrentIndex(0 if current == 'western' else 1)
        form.addRow('تنسيق الأرقام:', self.format_combo)
        self.abbreviate_check = QCheckBox('اختصار الأعداد الكبيرة (K, M)'); self.abbreviate_check.setChecked(currency.abbreviate_numbers())
        form.addRow(self.abbreviate_check)
        save_btn = QPushButton('حفظ إعدادات العملة'); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_currency_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group); layout.addStretch(); return scroll

    def create_rates_tab(self):
        scroll, layout = self._scroll_tab()
        group, box = self._card('أسعار الصرف', 'السعر هنا بصيغة: 1 دولار = قيمة العملة المختارة. يمكن تعديل السعر يدويًا أو جلبه من الإنترنت.')
        self.rates_table = QTableWidget(); self.rates_table.setColumnCount(3); self.rates_table.setHorizontalHeaderLabels(['العملة', 'السعر', 'آخر تحديث'])
        self.rates_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rates_table.setAlternatingRowColors(True); self.rates_table.setMinimumHeight(320)
        box.addWidget(self.rates_table)
        refresh_btn = QPushButton('تحديث الأسعار من الإنترنت'); refresh_btn.clicked.connect(self.fetch_online_rates)
        save_btn = QPushButton('حفظ إعدادات العملة والأسعار'); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_currency_settings)
        box.addLayout(self._button_row(refresh_btn, save_btn))
        layout.addWidget(group); layout.addStretch(); return scroll

    def create_network_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(
            'إعدادات الشبكة',
            'تم فصل وضع الاتصال عن تشغيل الخادم. اختر هل يعمل البرنامج محلياً، كعميل يتصل بخادم، أو كجهاز خادم، ثم شغّل خدمة الخادم يدوياً عند الحاجة.'
        )
        self.mode_combo = QComboBox(); self.mode_combo.addItems(['محلي (بدون شبكة)', 'عميل (اتصال بخادم)', 'خادم / قاعدة محلية مع خدمة اختيارية'])
        settings = QSettings('Alrajhi', 'Accounting')
        current_mode = settings.value('network/mode', 'local')
        self.mode_combo.setCurrentIndex({'local': 0, 'client': 1, 'server': 2}.get(current_mode, 0))
        form.addRow('وضع الاتصال:', self.mode_combo)

        self.server_url_edit = QLineEdit(settings.value('network/server_url', 'http://localhost:8000'))
        self.server_url_edit.setPlaceholderText('10.98.199.132 أو http://10.98.199.132:8000')
        form.addRow('عنوان الخادم للاتصال:', self.server_url_edit)

        self.server_port_spin = QSpinBox(); self.server_port_spin.setRange(1024, 65535); self.server_port_spin.setValue(int(settings.value('server/port', 8000)))
        form.addRow('منفذ الخادم المحلي:', self.server_port_spin)

        self.server_auto_start_check = QCheckBox('تشغيل الخادم المحلي تلقائياً عند بدء التطبيق')
        self.server_auto_start_check.setChecked(settings.value('server/auto_start', False, type=bool))
        form.addRow(self.server_auto_start_check)

        self.server_status_label = QLabel('')
        self.server_status_label.setWordWrap(True)
        form.addRow('حالة الخادم:', self.server_status_label)

        start_btn = QPushButton('▶ تشغيل الخادم الآن'); start_btn.clicked.connect(self.start_local_server_now)
        stop_btn = QPushButton('■ إيقاف الخادم'); stop_btn.clicked.connect(self.stop_local_server_now)
        refresh_btn = QPushButton('🔄 تحديث الحالة'); refresh_btn.clicked.connect(self.refresh_server_status)
        test_btn = QPushButton('اختبار الاتصال'); test_btn.clicked.connect(self.test_network_connection)
        form.addRow(self._button_row(start_btn, stop_btn, refresh_btn, test_btn))

        form.addRow(self._note(
            'ملاحظة: وضع “خادم” لا يعني تشغيل الخدمة تلقائياً. تشغيل الخدمة وإيقافها يتمان من هذه الأزرار أو عبر خيار التشغيل التلقائي.',
            'info'
        ))

        network_ok, network_msg = check_network_activation()
        if not network_ok:
            form.addRow(self._note(f'⚠️ {network_msg}. يلزم تفعيل ميزة الشبكة لاستخدام وضع العميل/الخادم.', 'warning'))
            activate_btn = QPushButton('🔓 تفعيل الشبكة'); activate_btn.clicked.connect(self.activate_network_dialog)
            form.addRow(self._button_row(activate_btn))
        save_btn = QPushButton('حفظ إعدادات الشبكة'); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_network_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group); layout.addStretch(); self.refresh_server_status(); return scroll

    def create_backup_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('النسخ الاحتياطي الدوري', 'تحديد مكان النسخ وجدولة النسخ التلقائي لقواعد البيانات المحلية.')
        self.backup_enabled = QCheckBox('تفعيل النسخ التلقائي'); form.addRow(self.backup_enabled)
        self.backup_interval = QSpinBox(); self.backup_interval.setRange(1, 24); self.backup_interval.setSuffix(' ساعة')
        form.addRow('كل:', self.backup_interval)
        self.backup_folder = QLineEdit(); self.backup_folder.setPlaceholderText('اختر مجلد النسخ الاحتياطي')
        browse_btn = QPushButton('استعراض'); browse_btn.clicked.connect(self.browse_backup_folder)
        row = QHBoxLayout(); row.addWidget(self.backup_folder, 1); row.addWidget(browse_btn)
        form.addRow('مجلد الوجهة:', row)
        save_backup_btn = QPushButton('حفظ إعدادات النسخ الاحتياطي'); save_backup_btn.setObjectName('primary'); save_backup_btn.clicked.connect(self.save_backup_settings)
        form.addRow(self._button_row(save_backup_btn)); layout.addWidget(group)
        instant_group, instant_box = self._card('نسخ احتياطي فوري', 'إنشاء نسخة آمنة الآن باستخدام SQLite online backup مع فحص سلامة الملف.')
        backup_now_btn = QPushButton('📀 إنشاء نسخة احتياطية الآن'); backup_now_btn.setObjectName('primary'); backup_now_btn.clicked.connect(self.create_backup_now)
        instant_box.addLayout(self._button_row(backup_now_btn)); layout.addWidget(instant_group)
        manage_group, manage_box = self._card('إدارة قاعدة البيانات', 'التصدير والاستيراد وإعادة التهيئة عمليات حساسة. يتم إنشاء نسخة وقائية قبل الاستعادة أو إعادة التهيئة.')
        manage_layout = QHBoxLayout()
        self.export_btn = QPushButton('📤 تصدير قاعدة البيانات'); self.export_btn.clicked.connect(self.export_database)
        self.import_btn = QPushButton('📥 استيراد قاعدة البيانات'); self.import_btn.clicked.connect(self.import_database)
        self.reset_btn = QPushButton('⚠️ إعادة تهيئة قاعدة البيانات'); self.reset_btn.setObjectName('danger'); self.reset_btn.clicked.connect(self.reset_database)
        manage_layout.addWidget(self.export_btn); manage_layout.addWidget(self.import_btn); manage_layout.addWidget(self.reset_btn)
        manage_box.addLayout(manage_layout); layout.addWidget(manage_group)
        layout.addStretch(); self.load_backup_settings(); return scroll

    def save_appearance_settings(self):
        theme = self.theme_combo.currentData() or 'light'
        settings_service.set_theme(theme); ThemeManager.apply_theme(theme, persist=True)
        main_window = self.window()
        if hasattr(main_window, 'top_bar') and hasattr(main_window.top_bar, 'apply_styles'): main_window.top_bar.apply_styles()
        for page in getattr(main_window, 'pages', {}).values():
            if hasattr(page, 'apply_theme_colors'): page.apply_theme_colors()
        show_toast('تم تطبيق المظهر', 'success', self)

    def save_printing_settings(self):
        settings_service.save_printing_settings(
            invoice_template=self.print_invoice_template.currentData() or 'a4',
            report_template=self.print_report_template.currentData() or 'a4',
            voucher_template=self.print_voucher_template.currentData() or 'a4',
            return_template=self.print_return_template.currentData() or 'a4',
            show_logo=self.print_show_logo.isChecked(),
            show_tax_number=self.print_show_tax.isChecked(),
            show_qr=self.print_show_qr.isChecked(),
            footer_text=self.print_footer.text().strip(),
            thermal_size=self.print_thermal_size.currentText(),
            font_family=self.print_font_family.text().strip(),
            font_size=self.print_font_size.currentText(),
            accent_color=self.print_accent_color.text().strip(),
            zebra_rows=self.print_zebra_rows.isChecked(),
            compact_tables=self.print_compact_tables.isChecked(),
        )
        show_toast('تم حفظ إعدادات الطباعة الموحدة', 'success', self)

    def browse_logo(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'اختر شعار الشركة', '', 'Images (*.png *.jpg *.jpeg *.bmp)')
        if filename: self.company_logo_path_edit.setText(filename)

    def save_company_info(self):
        from config import save_company_info
        info = {'name': self.company_name_edit.text().strip(), 'address': self.company_address_edit.text().strip(), 'phone': self.company_phone_edit.text().strip(), 'email': self.company_email_edit.text().strip(), 'tax_number': self.company_tax_number_edit.text().strip(), 'logo_path': self.company_logo_path_edit.text().strip()}
        audit_service.log('UPDATE', 'SETTINGS_COMPANY', None, new_values=info, details='تعديل معلومات الشركة')
        save_company_info(info); show_toast('تم حفظ معلومات الشركة', 'success', self)

    def browse_backup_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'اختر مجلد النسخ الاحتياطي')
        if folder: self.backup_folder.setText(folder)

    def save_backup_settings(self):
        from database.connection import DatabaseConnection
        if DatabaseConnection().is_remote(): QMessageBox.warning(self, 'تنبيه', 'لا يمكن حفظ إعدادات النسخ الاحتياطي في وضع العميل.'); return
        settings = QSettings('Alrajhi', 'Accounting')
        old = {
            'backup/enabled': settings.value('backup/enabled', False, type=bool),
            'backup/interval_hours': settings.value('backup/interval_hours', 6, type=int),
            'backup/folder': settings.value('backup/folder', ''),
        }
        new = {
            'backup/enabled': self.backup_enabled.isChecked(),
            'backup/interval_hours': self.backup_interval.value(),
            'backup/folder': self.backup_folder.text(),
        }
        settings.setValue('backup/enabled', new['backup/enabled']); settings.setValue('backup/interval_hours', new['backup/interval_hours']); settings.setValue('backup/folder', new['backup/folder'])
        audit_service.log('UPDATE', 'SETTINGS_BACKUP', None, old_values=old, new_values=new, details='تعديل إعدادات النسخ الاحتياطي')
        show_toast('تم حفظ إعدادات النسخ الاحتياطي', 'success', self)

    def load_backup_settings(self):
        settings = QSettings('Alrajhi', 'Accounting')
        self.backup_enabled.setChecked(settings.value('backup/enabled', False, type=bool)); self.backup_interval.setValue(settings.value('backup/interval_hours', 6, type=int)); self.backup_folder.setText(settings.value('backup/folder', ''))

    def create_backup_now(self):
        if backup_service.is_remote(): QMessageBox.warning(self, 'تنبيه', 'لا يمكن إنشاء نسخة احتياطية من جهاز عميل.'); return
        folder = self.backup_folder.text().strip()
        if not folder: QMessageBox.warning(self, 'خطأ', 'يرجى تحديد مجلد النسخ الاحتياطي أولاً'); return
        try:
            result = backup_service.create_backup(folder); sep = chr(10)
            QMessageBox.information(self, 'نجاح', f"تم إنشاء النسخة الاحتياطية وفحص سلامتها:{sep}{result['backup_path']}{sep}{sep}SHA256:{sep}{result['sha256']}")
        except Exception as e: QMessageBox.critical(self, 'خطأ', f'فشل النسخ الاحتياطي: {str(e)}')

    def export_database(self):
        if backup_service.is_remote(): QMessageBox.warning(self, 'تنبيه', 'لا يمكن تصدير قاعدة البيانات في وضع العميل.'); return
        filename, _ = QFileDialog.getSaveFileName(self, 'تصدير قاعدة البيانات', 'alrajhi_backup.db', 'SQLite (*.db)')
        if filename:
            try:
                result = backup_service.export_database(filename); QMessageBox.information(self, 'نجاح', f"تم التصدير وفحص سلامة الملف:{chr(10)}{result['backup_path']}")
            except Exception as e: QMessageBox.critical(self, 'خطأ', f'فشل التصدير: {str(e)}')

    def import_database(self):
        if backup_service.is_remote(): QMessageBox.warning(self, 'تنبيه', 'لا يمكن استيراد قاعدة البيانات في وضع العميل.'); return
        filename, _ = QFileDialog.getOpenFileName(self, 'استيراد قاعدة البيانات', '', 'SQLite (*.db)')
        if filename:
            try: backup_service.validate_backup(filename)
            except Exception as e: QMessageBox.critical(self, 'خطأ', f'ملف النسخة غير صالح أو تالف:{chr(10)}{str(e)}'); return
            reply = QMessageBox.question(self, 'تأكيد', 'سيتم استبدال قاعدة البيانات المحلية الحالية بعد إنشاء نسخة احتياطية وقائية. استمرار؟', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    result = backup_service.restore_backup(filename, create_pre_restore_backup=True); sep = chr(10); msg = 'تم الاستيراد. يرجى إعادة تشغيل التطبيق.'
                    if result.get('pre_restore_backup'): msg += f"{sep}{sep}نسخة وقائية قبل الاستعادة:{sep}{result['pre_restore_backup']}"
                    QMessageBox.information(self, 'نجاح', msg)
                except Exception as e: QMessageBox.critical(self, 'خطأ', f'فشل الاستيراد: {str(e)}')

    def reset_database(self):
        from database.connection import DatabaseConnection, DB_PATH
        if DatabaseConnection().is_remote(): QMessageBox.warning(self, 'تنبيه', 'لا يمكن إعادة تهيئة قاعدة البيانات في وضع العميل.'); return
        reply = QMessageBox.question(self, 'تأكيد خطير', 'سيتم حذف كل البيانات وإعادة تهيئة قاعدة البيانات. سيتم إنشاء نسخة وقائية قبل الحذف. متابعة؟', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                pre_reset = None
                if os.path.exists(DB_PATH): pre_reset = backup_service.create_backup(os.path.join(os.path.dirname(DB_PATH), 'pre_reset_backups'), prefix='alrajhi_pre_reset')['backup_path']
                db_conn = DatabaseConnection(); db_conn.close()
                if os.path.exists(DB_PATH): os.remove(DB_PATH)
                from database.migrations import init_database
                init_database(); msg = 'تم إعادة تهيئة قاعدة البيانات. يرجى إعادة تشغيل التطبيق.'
                if pre_reset: msg += f"{chr(10)}{chr(10)}نسخة وقائية قبل التهيئة:{chr(10)}{pre_reset}"
                QMessageBox.information(self, 'نجاح', msg)
            except Exception as e: QMessageBox.critical(self, 'خطأ', f'فشل إعادة التهيئة: {str(e)}')

    def load_rates_table(self):
        rates = currency.get_all_currencies(); self.rates_table.setRowCount(len(rates))
        for row, r in enumerate(rates):
            self.rates_table.setItem(row, 0, QTableWidgetItem(r['currency_code']))
            rate_item = QTableWidgetItem(f"{float(r['rate_to_usd']):.4f}"); rate_item.setFlags(rate_item.flags() | Qt.ItemIsEditable)
            self.rates_table.setItem(row, 1, rate_item); self.rates_table.setItem(row, 2, QTableWidgetItem(r['updated_at'][:19] if r.get('updated_at') else ''))

    def save_currency_settings(self):
        base_curr = self.base_curr.currentText(); display_curr = self.display_curr.currentText(); decimals = self.decimals.value(); fmt = 'western' if self.format_combo.currentIndex() == 0 else 'arabic'; abbrev_bool = self.abbreviate_check.isChecked()
        old_currency = self.settings.get_currency_settings()
        for row in range(self.rates_table.rowCount()):
            code_item = self.rates_table.item(row, 0); rate_item = self.rates_table.item(row, 1)
            if not code_item or not rate_item: continue
            code = code_item.text(); rate_text = rate_item.text(); clean_rate_text = rate_text.replace(',', '').replace(' ', '').strip()
            try: currency.update_rate(code, float(clean_rate_text))
            except ValueError: QMessageBox.warning(self, 'خطأ', f'سعر غير صالح للعملة {code}: {rate_text}'); return
        rates_payload = []
        for row in range(self.rates_table.rowCount()):
            code_item = self.rates_table.item(row, 0); rate_item = self.rates_table.item(row, 1)
            if code_item and rate_item:
                rates_payload.append({'currency_code': code_item.text(), 'rate': rate_item.text()})
        self.settings.save_currency_settings(base_curr, display_curr, decimals, fmt, abbrev_bool)
        audit_service.log('UPDATE', 'CURRENCY_RATES', None, old_values=old_currency, new_values={'rates': rates_payload}, details='تعديل أسعار الصرف')
        QMessageBox.information(self, 'نجاح', 'تم حفظ إعدادات العملة وأسعار الصرف'); self.currency_settings_changed.emit()
        main_window = self.window()
        if hasattr(main_window, 'pages') and 'dashboard' in main_window.pages and hasattr(main_window.pages['dashboard'], 'reload_from_settings'): main_window.pages['dashboard'].reload_from_settings()

    def fetch_online_rates(self):
        try:
            resp = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
            if resp.status_code == 200:
                rates = resp.json().get('rates', {})
                for row in range(self.rates_table.rowCount()):
                    code = self.rates_table.item(row, 0).text()
                    if code in rates: self.rates_table.item(row, 1).setText(f"{rates[code]:.4f}")
                QMessageBox.information(self, 'نجاح', 'تم تحديث الأسعار من الإنترنت')
            else: QMessageBox.warning(self, 'خطأ', 'فشل الاتصال بالخادم')
        except Exception as e: QMessageBox.warning(self, 'خطأ', f'حدث خطأ: {str(e)}')

    def activate_network_dialog(self):
        dialog = QDialog(self); dialog.setWindowTitle('تفعيل الشبكة'); dialog.setLayoutDirection(Qt.RightToLeft); dialog.resize(460, 220)
        layout = QVBoxLayout(dialog); layout.addWidget(self._note('أدخل مفتاح تفعيل ميزة الشبكة. بعد التفعيل أعد تشغيل التطبيق لتحديث وضع التشغيل.', 'info'))
        key_edit = QLineEdit(); key_edit.setEchoMode(QLineEdit.Password); key_edit.setPlaceholderText('مفتاح التفعيل'); layout.addWidget(key_edit)
        status_label = QLabel(); status_label.setStyleSheet('color: red;'); layout.addWidget(status_label)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._do_activate_network(key_edit.text().strip(), status_label, dialog)); button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box); dialog.exec()

    def _do_activate_network(self, key, status_label, dialog):
        if not key: status_label.setText('يرجى إدخال مفتاح التفعيل'); return
        success, msg = activate_network(key)
        if success:
            audit_service.log('ACTIVATE', 'NETWORK', None, new_values={'activated': True}, details='تفعيل ميزة الشبكة')
            QMessageBox.information(self, 'نجاح', 'تم تفعيل الشبكة. يرجى إعادة تشغيل التطبيق.'); dialog.accept()
        else: status_label.setText(f'فشل: {msg}')

    def refresh_server_status(self):
        if not hasattr(self, 'server_status_label'):
            return
        running, msg = server_status()
        self.server_status_label.setText(('✅ ' if running else '⚪ ') + msg)
        self.server_status_label.setStyleSheet('color:#15803d;' if running else 'color:#475569;')

    def start_local_server_now(self):
        settings = QSettings('Alrajhi', 'Accounting')
        settings.setValue('server/port', self.server_port_spin.value())
        settings.sync()
        ok, msg = start_server_process(port=self.server_port_spin.value())
        QMessageBox.information(self, 'تشغيل الخادم' if ok else 'تعذر تشغيل الخادم', msg)
        self.refresh_server_status()

    def stop_local_server_now(self):
        ok, msg = stop_server_process()
        QMessageBox.information(self, 'إيقاف الخادم' if ok else 'تعذر إيقاف الخادم', msg)
        self.refresh_server_status()

    def test_network_connection(self):
        raw = self.server_url_edit.text().strip()
        port = self.server_port_spin.value()
        url = normalize_server_url(raw, port)
        ok, message, info = server_diagnostics(url, timeout=4, require_routes=True)
        self.server_url_edit.setText(url)
        details = f"العنوان المستخدم:\n{url}\n\n{message}"
        if ok:
            QMessageBox.information(self, 'اختبار الاتصال', f'✅ الاتصال ناجح ومتوافق.\n\n{details}')
        else:
            QMessageBox.warning(self, 'اختبار الاتصال', f'❌ فشل اختبار الاتصال.\n\n{details}')


    def save_network_settings(self):
        mode = {0: 'local', 1: 'client', 2: 'server'}[self.mode_combo.currentIndex()]
        settings = QSettings('Alrajhi', 'Accounting')
        old = {
            'network/mode': settings.value('network/mode', 'local'),
            'network/server_url': settings.value('network/server_url', ''),
            'server/port': settings.value('server/port', 8000),
            'server/auto_start': settings.value('server/auto_start', False, type=bool),
        }
        port = self.server_port_spin.value() if hasattr(self, 'server_port_spin') else 8000
        url = normalize_server_url(self.server_url_edit.text().strip(), port)
        new = {
            'network/mode': mode,
            'network/server_url': url,
            'server/port': port,
            'server/auto_start': self.server_auto_start_check.isChecked() if hasattr(self, 'server_auto_start_check') else False,
        }
        settings.setValue('network/mode', mode)
        settings.setValue('network/server_url', url)
        settings.setValue('server/port', port)
        settings.setValue('server/auto_start', new['server/auto_start'])
        settings.sync()
        audit_service.log('UPDATE', 'SETTINGS_NETWORK', None, old_values=old, new_values=new, details='تعديل إعدادات الشبكة والخادم')
        QMessageBox.information(self, 'تم الحفظ', 'تم حفظ إعدادات الشبكة. قد تحتاج لإعادة تشغيل التطبيق لتغيير وضع الاتصال.')
        self.refresh_server_status()
