# -*- coding: utf-8 -*-
from database.connection import DatabaseConnection
from core.services.settings_service import settings_service
import datetime
from decimal import Decimal

class CurrencyManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_base_currency(self) -> str:
        return settings_service.get('base_currency', 'USD')
    
    def get_display_currency(self) -> str:
        return settings_service.get('display_currency', 'USD')
    
    def get_currency_symbol(self, currency_code: str = None) -> str:
        if currency_code is None:
            currency_code = self.get_display_currency()
        symbols = {
            'USD': '$', 'SAR': '﷼', 'SYP': 'ل.س', 'EUR': '€', 'GBP': '£',
            'AED': 'د.إ', 'QAR': 'ر.ق', 'KWD': 'د.ك', 'OMR': 'ر.ع.',
        }
        return symbols.get(currency_code, currency_code)
    
    def get_currency_decimals(self) -> int:
        return int(settings_service.get('currency_decimals', '2'))
    
    def get_number_format(self) -> str:
        return settings_service.get('number_format', 'western')
    
    def abbreviate_numbers(self) -> bool:
        return settings_service.get('abbreviate_numbers', 'false').lower() == 'true'
    
    def get_current_rate(self, currency_code: str) -> Decimal:
        if currency_code == 'USD':
            return Decimal('1.0')
        db = DatabaseConnection()
        if db.is_remote():
            rates = db.get_all_currencies()
            for r in rates:
                if r['currency_code'] == currency_code:
                    return Decimal(str(r['rate_to_usd']))
            return Decimal('1.0')
        else:
            conn = db.get_connection()
            row = conn.execute("SELECT rate_to_usd FROM exchange_rates WHERE currency_code=?", (currency_code,)).fetchone()
            if row:
                return Decimal(str(row['rate_to_usd']))
            return Decimal('1.0')
    
    def get_historical_rate(self, currency_code: str, date: str) -> Decimal:
        if currency_code == 'USD':
            return Decimal('1.0')
        db = DatabaseConnection()
        if db.is_remote():
            if db.get_rest_client():
                rate = db.get_rest_client().get_historical_rate(currency_code, date)
                return Decimal(str(rate)) if rate else Decimal('1.0')
            return Decimal('1.0')
        else:
            conn = db.get_connection()
            row = conn.execute("""
                SELECT rate_to_usd FROM exchange_rate_history
                WHERE currency_code = ? AND effective_date <= ?
                ORDER BY effective_date DESC LIMIT 1
            """, (currency_code, date)).fetchone()
            if row:
                return Decimal(str(row['rate_to_usd']))
            return Decimal('1.0')
    
    def convert(self, amount, from_currency: str, to_currency: str, date: str = None):
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if from_currency == to_currency:
            return amount
        if date:
            rate_from = self.get_historical_rate(from_currency, date)
            rate_to = self.get_historical_rate(to_currency, date)
        else:
            rate_from = self.get_current_rate(from_currency)
            rate_to = self.get_current_rate(to_currency)
        if rate_from == 0 or rate_to == 0:
            return amount
        amount_usd = amount / rate_from
        return amount_usd * rate_to
    
    def update_rate(self, currency_code: str, rate_to_usd: float):
        """تحديث سعر الصرف الحالي (يُستخدم من settings_widget.py)"""
        db = DatabaseConnection()
        db.update_exchange_rate(currency_code, rate_to_usd)
    
    def _abbreviate_number(self, num: Decimal) -> str:
        num_float = float(num)
        if num_float >= 1_000_000_000:
            return f"{num_float / 1_000_000_000:.1f}B"
        elif num_float >= 1_000_000:
            return f"{num_float / 1_000_000:.1f}M"
        elif num_float >= 1_000:
            return f"{num_float / 1_000:.1f}K"
        else:
            formatted = f"{num:.2f}".rstrip('0').rstrip('.')
            return formatted if '.' in formatted else f"{num:.0f}"
    
    def format_amount(self, amount, currency_code: str = None, decimals: int = None) -> str:
        if currency_code is None:
            currency_code = self.get_display_currency()
        if decimals is None:
            decimals = self.get_currency_decimals()
        symbol = self.get_currency_symbol(currency_code)
        fmt = self.get_number_format()
        abbrev = self.abbreviate_numbers()
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if abbrev and abs(amount) >= 1000:
            formatted = self._abbreviate_number(amount)
        else:
            formatted = f"{amount:,.{decimals}f}"
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
        if fmt == 'arabic':
            formatted = formatted.replace('0', '٠').replace('1', '١').replace('2', '٢').replace('3', '٣').replace('4', '٤')\
                                 .replace('5', '٥').replace('6', '٦').replace('7', '٧').replace('8', '٨').replace('9', '٩')
        return f"{formatted} {symbol}"
    
    def get_all_currencies(self) -> list:
        db = DatabaseConnection()
        return db.get_all_currencies()

currency = CurrencyManager()


