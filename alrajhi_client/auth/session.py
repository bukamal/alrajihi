# -*- coding: utf-8 -*-
from typing import Optional, Dict
import base64
import hashlib
from cryptography.fernet import Fernet
from PyQt5.QtCore import QSettings

class UserSession:
    _current_user: Optional[Dict] = None
    _current_user_id: Optional[str] = None
    _current_user_role: Optional[str] = None
    _force_password_change: bool = False

    @classmethod
    def login(cls, user: Dict):
        cls._current_user = user
        cls._current_user_id = user.get('id')
        cls._current_user_role = user.get('role')
        cls._force_password_change = user.get('force_password_change', 0) == 1

    @classmethod
    def logout(cls):
        cls._current_user = None
        cls._current_user_id = None
        cls._current_user_role = None
        cls._force_password_change = False

    @classmethod
    def get_current(cls) -> Optional[Dict]:
        return cls._current_user

    @classmethod
    def get_current_user_id(cls) -> Optional[str]:
        return cls._current_user_id

    @classmethod
    def get_current_user_role(cls) -> Optional[str]:
        return cls._current_user_role

    @classmethod
    def get_current_branch_id(cls):
        user = cls.get_current() or {}
        branch_id = user.get('branch_id')
        try:
            return int(branch_id) if branch_id not in (None, '', 0, '0') else None
        except Exception:
            return None

    @classmethod
    def set_current_branch_id(cls, branch_id):
        if cls._current_user is not None:
            cls._current_user['branch_id'] = branch_id

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._current_user is not None

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user and cls._current_user.get('role') == 'admin'

    @classmethod
    def force_password_change(cls) -> bool:
        return cls._force_password_change

    @classmethod
    def set_force_password_change(cls, value: bool):
        cls._force_password_change = value
        if cls._current_user:
            cls._current_user['force_password_change'] = 1 if value else 0

    # ========== دوال الصلاحيات الخاصة بالتصنيع ==========
    @classmethod
    def can_manage_production(cls) -> bool:
        user = cls.get_current()
        if not user:
            return False
        role = user.get('role', '')
        return role in ('admin', 'manufacturing_manager', 'production_manager')

    @classmethod
    def can_reverse_production(cls) -> bool:
        user = cls.get_current()
        if not user:
            return False
        role = user.get('role', '')
        return role in ('admin', 'manufacturing_manager')


# ========== إدارة التوكن المشفر ==========
def _get_encryption_key():
    from auth.activation import get_device_id
    device_id = get_device_id()
    salt = b'alrajhi_token_salt_2024'
    # استخدام hashlib بدلاً من cryptography.hazmat.primitives.kdf.pbkdf2 لضمان التوافق
    key = hashlib.pbkdf2_hmac('sha256', device_id.encode(), salt, 100000, dklen=32)
    return base64.urlsafe_b64encode(key)

def save_token(token: str):
    key = _get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(token.encode())
    settings = QSettings("Alrajhi", "Accounting")
    settings.setValue("auth/token", encrypted)

def load_token() -> str | None:
    settings = QSettings("Alrajhi", "Accounting")
    encrypted = settings.value("auth/token")
    if not encrypted:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    try:
        token = f.decrypt(encrypted).decode()
        return token
    except:
        return None

def clear_token():
    settings = QSettings("Alrajhi", "Accounting")
    settings.remove("auth/token")


