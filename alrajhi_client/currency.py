# -*- coding: utf-8 -*-
from gateways.currency_gateway import create_currency_gateway
from decimal import Decimal
import json
from PyQt5.QtCore import QSettings


def _settings_service():
    """Return the settings service lazily.

    currency.py is imported by some repository modules while settings_service is
    still being initialized during application startup.  Importing
    settings_service at module load time creates a circular import:

        settings_service -> local settings gateway -> settings repository package
        -> expense_repo -> currency -> settings_service

    Keeping this import lazy preserves the existing CurrencyManager API while
    making startup deterministic.
    """
    from core.services.settings_service import settings_service
    return settings_service


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
            cls._instance._gateway = None
            cls._instance._settings = QSettings("Alrajhi", "Accounting")
        return cls._instance

    @property
    def gateway(self):
        if self._gateway is None:
            self._gateway = create_currency_gateway()
        return self._gateway
    
    def get_base_currency(self) -> str:
        return _settings_service().get('base_currency', 'USD')
    
    def get_display_currency(self) -> str:
        return _settings_service().get('display_currency', 'USD')
    
    def get_currency_symbol(self, currency_code: str = None) -> str:
        if currency_code is None:
            currency_code = self.get_display_currency()
        symbols = {
            'USD': '$', 'SAR': '﷼', 'SYP': 'ل.س', 'EUR': '€', 'GBP': '£',
            'AED': 'د.إ', 'QAR': 'ر.ق', 'KWD': 'د.ك', 'OMR': 'ر.ع.',
        }
        return symbols.get(currency_code, currency_code)
    
    def get_currency_decimals(self) -> int:
        return int(_settings_service().get('currency_decimals', '2'))
    
    def get_number_format(self) -> str:
        return _settings_service().get('number_format', 'western')
    
    def abbreviate_numbers(self) -> bool:
        return str(_settings_service().get('abbreviate_numbers', 'false')).lower() == 'true'
    
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
        from_currency = str(from_currency or self.get_base_currency() or 'USD')
        to_currency = str(to_currency or self.get_display_currency() or from_currency)
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
        amount_base = amount / rate_from
        return amount_base * rate_to

    def storage_currency(self) -> str:
        """Currency used by persisted monetary amounts.

        Older code historically used USD directly.  New UI code should call this
        method instead of hard-coding USD so future base-currency changes stay
        localized.
        """
        return str(self.get_base_currency() or 'USD')

    def display_currency(self) -> str:
        return str(self.get_display_currency() or self.storage_currency())

    def to_display(self, amount, from_currency: str = None, date: str = None):
        """Convert a persisted/base amount to the current display currency."""
        return self.convert(amount, from_currency or self.storage_currency(), self.display_currency(), date=date)

    def from_display(self, amount, to_currency: str = None, date: str = None):
        """Convert a UI/display amount back to the persisted/base currency."""
        return self.convert(amount, self.display_currency(), to_currency or self.storage_currency(), date=date)

    def format_display_amount(self, amount, currency_code: str = None, decimals: int = None) -> str:
        return self.format_amount(amount, currency_code or self.display_currency(), decimals=decimals)

    def format_base_amount(self, amount, from_currency: str = None, decimals: int = None) -> str:
        return self.format_amount(self.to_display(amount, from_currency=from_currency), self.display_currency(), decimals=decimals)
    
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
        """Format a display-currency amount through the unified money policy.

        This method intentionally does not convert.  Callers that hold base or
        storage amounts must call ``to_display``/``convert`` first, then format
        the already-displayed amount here.
        """
        try:
            from core.money_display_policy import format_money
            return format_money(
                amount,
                currency_code or self.get_display_currency(),
                decimals=self.get_currency_decimals() if decimals is None else decimals,
            )
        except Exception:
            if currency_code is None:
                currency_code = self.get_display_currency()
            if decimals is None:
                decimals = self.get_currency_decimals()
            symbol = self.get_currency_symbol(currency_code)
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount or 0))
            formatted = f"{amount:,.{decimals}f}"
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


