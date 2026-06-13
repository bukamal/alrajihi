# -*- coding: utf-8 -*-
from gateways.currency_gateway import create_currency_gateway
from core.services.settings_service import settings_service
from decimal import Decimal
import json
from PyQt5.QtCore import QSettings

class CurrencyManager:
    _instance = None
    DEFAULT_RATES = {
        'USD': Decimal('1.0'), 'SAR': Decimal('3.75'), 'SYP': Decimal('14000.0'),
        'EUR': Decimal('0.92'), 'GBP': Decimal('0.79'), 'AED': Decimal('3.67'),
        'QAR': Decimal('3.64'), 'KWD': Decimal('0.31'), 'OMR': Decimal('0.38'),
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.gateway = create_currency_gateway()
            cls._instance._settings = QSettings("Alrajhi", "Accounting")
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
    
    def _load_rate_cache(self) -> dict:
        raw = self._settings.value('currency/rate_cache_json', '{}')
        try:
            data = json.loads(raw or '{}') if isinstance(raw, str) else {}
        except Exception:
            data = {}
        return data if isinstance(data, dict) else {}

    def _save_rate_cache(self, rates: dict) -> None:
        try:
            self._settings.setValue('currency/rate_cache_json', json.dumps(rates, ensure_ascii=False))
        except Exception:
            pass

    def _cache_rate(self, currency_code: str, rate) -> None:
        if rate is None:
            return
        try:
            rates = self._load_rate_cache()
            rates[str(currency_code)] = str(rate)
            self._save_rate_cache(rates)
        except Exception:
            pass

    def _cached_or_default_rate(self, currency_code: str) -> Decimal:
        code = str(currency_code or 'USD')
        rates = self._load_rate_cache()
        if code in rates:
            try:
                return Decimal(str(rates[code]))
            except Exception:
                pass
        return self.DEFAULT_RATES.get(code, Decimal('1.0'))

    def get_current_rate(self, currency_code: str) -> Decimal:
        code = str(currency_code or 'USD')
        if code == 'USD':
            return Decimal('1.0')
        try:
            rate = self.gateway.get_current_rate(code)
            if rate is not None:
                self._cache_rate(code, rate)
                return Decimal(str(rate))
        except Exception as exc:
            print(f"⚠️ تعذر جلب سعر الصرف من الخادم؛ سيتم استخدام آخر سعر محفوظ لـ {code}: {exc}")
        return self._cached_or_default_rate(code)
    
    def get_historical_rate(self, currency_code: str, date: str) -> Decimal:
        code = str(currency_code or 'USD')
        if code == 'USD':
            return Decimal('1.0')
        try:
            rate = self.gateway.get_historical_rate(code, date)
            if rate is not None:
                self._cache_rate(code, rate)
                return Decimal(str(rate))
        except Exception as exc:
            print(f"⚠️ تعذر جلب سعر الصرف التاريخي من الخادم؛ سيتم استخدام آخر سعر محفوظ لـ {code}: {exc}")
        return self._cached_or_default_rate(code)
    
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
        self.gateway.update_rate(currency_code, rate_to_usd)
    
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
        try:
            rows = self.gateway.get_all_currencies()
            for row in rows or []:
                code = row.get('currency_code')
                rate = row.get('rate_to_usd')
                if code and rate is not None:
                    self._cache_rate(code, rate)
            if rows:
                return rows
        except Exception as exc:
            print(f"⚠️ تعذر جلب قائمة العملات من الخادم؛ سيتم استخدام الكاش المحلي: {exc}")
        cached = self._load_rate_cache()
        if not cached:
            cached = {code: str(rate) for code, rate in self.DEFAULT_RATES.items()}
        return [{'currency_code': code, 'rate_to_usd': str(rate), 'updated_at': None, 'cached': True} for code, rate in sorted(cached.items())]

currency = CurrencyManager()


