import os
import json
import hashlib
import base64
import platform
import getpass
import threading
import time
import requests
from typing import Tuple, Optional, Callable
from core.app_paths import license_file, network_license_file, feature_license_file
from auth.license_security import build_license_record, validate_license_record

SERVER_URL = 'https://license.manhal-almasriiii199119.workers.dev/activate'
LICENSE_FILE = str(license_file())
NETWORK_LICENSE_FILE = str(network_license_file())

FEATURE_ACTIVATION_IDS = {
    'network': 'network',
    'manufacturing': 'manufacturing',
    'restaurant': 'restaurant',
    'cafe': 'cafe',
    'apparel': 'apparel',
}

def normalize_feature_activation_id(feature: str | None) -> str:
    value = str(feature or '').strip().lower().replace(' ', '_').replace('-', '_')
    aliases = {
        'manufacturing_interface': 'manufacturing',
        'restaurant_interface': 'restaurant',
        'café': 'cafe',
        'coffee': 'cafe',
        'cafe_interface': 'cafe',
        'apparel_interface': 'apparel',
        'clothes': 'apparel',
        'network_feature': 'network',
    }
    value = aliases.get(value, value)
    return FEATURE_ACTIVATION_IDS.get(value, value)

def _feature_license_path(feature: str) -> str:
    feature_id = normalize_feature_activation_id(feature)
    return str(feature_license_file(feature_id))

def get_device_id() -> str:
    try:
        username = getpass.getuser()
    except:
        username = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
    info = platform.node() + platform.processor() + username + platform.system() + platform.machine()
    return hashlib.sha256(info.encode()).hexdigest()

def _derive_key(device_id: str, salt: bytes = b'alrajhi_salt_2025') -> bytes:
    return hashlib.pbkdf2_hmac('sha256', device_id.encode(), salt, 100000, dklen=32)

def _xor_encrypt_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

def _encrypt_license(data: dict, device_id: str) -> str:
    key = _derive_key(device_id)
    plaintext = json.dumps(data).encode()
    encrypted = _xor_encrypt_decrypt(plaintext, key)
    return base64.b64encode(encrypted).decode()

def _decrypt_license(encrypted: str, device_id: str) -> Optional[dict]:
    try:
        key = _derive_key(device_id)
        enc_bytes = base64.b64decode(encrypted)
        plaintext = _xor_encrypt_decrypt(enc_bytes, key)
        return json.loads(plaintext.decode())
    except:
        return None

def activate(license_key: str) -> Tuple[bool, str]:
    device_id = get_device_id()
    try:
        resp = requests.post(SERVER_URL, json={'licenseCode': license_key, 'fingerprint': device_id}, timeout=15)
        if resp.status_code != 200:
            return False, resp.text or "فشل التفعيل"
        result = resp.json()
        data = build_license_record(license_key=license_key, device_id=device_id, server_result=result)
        with open(LICENSE_FILE, 'w') as f:
            f.write(_encrypt_license(data, device_id))
        return True, ""
    except Exception as e:
        return False, str(e)

def check_activation() -> Tuple[bool, str]:
    if not os.path.exists(LICENSE_FILE):
        return False, "لم يتم التفعيل"
    try:
        with open(LICENSE_FILE, 'r') as f:
            encrypted = f.read().strip()
        device_id = get_device_id()
        data = _decrypt_license(encrypted, device_id)
        ok, message = validate_license_record(data, expected_device=device_id)
        if not ok:
            return False, message
        return True, ""
    except Exception as e:
        return False, str(e)

def activate_feature(feature: str, license_key: str) -> Tuple[bool, str]:
    feature_id = normalize_feature_activation_id(feature)
    device_id = get_device_id()
    try:
        resp = requests.post(
            SERVER_URL,
            json={'licenseCode': license_key, 'fingerprint': device_id, 'feature': feature_id},
            timeout=15,
        )
        if resp.status_code != 200:
            return False, resp.text or f"فشل تفعيل {feature_id}"
        result = resp.json()
        data = build_license_record(license_key=license_key, device_id=device_id, server_result=result, feature_id=feature_id)
        with open(_feature_license_path(feature_id), 'w') as f:
            f.write(_encrypt_license(data, device_id))
        return True, ""
    except Exception as e:
        return False, str(e)

def check_feature_activation(feature: str) -> Tuple[bool, str]:
    feature_id = normalize_feature_activation_id(feature)
    path = _feature_license_path(feature_id)
    if not os.path.exists(path):
        return False, f"ميزة {feature_id} غير مفعلة"
    try:
        with open(path, 'r') as f:
            encrypted = f.read().strip()
        device_id = get_device_id()
        data = _decrypt_license(encrypted, device_id)
        ok, message = validate_license_record(data, expected_device=device_id, expected_feature=feature_id)
        if not ok:
            return False, message
        return True, ""
    except Exception as e:
        return False, str(e)

def activate_network(license_key: str) -> Tuple[bool, str]:
    return activate_feature('network', license_key)

def check_network_activation() -> Tuple[bool, str]:
    ok, message = check_feature_activation('network')
    if not ok and 'network' in str(message):
        return False, "ميزة الشبكة غير مفعلة" if 'غير مفعلة' in str(message) else "ترخيص الشبكة غير صالح"
    return ok, message

_license_checker_thread = None
_license_checker_stop = False
_on_invalid = None

def start_license_checker(interval_hours: int = 24, on_invalid: Callable = None):
    global _license_checker_thread, _license_checker_stop, _on_invalid
    _license_checker_stop = False
    _on_invalid = on_invalid
    def loop():
        while not _license_checker_stop:
            time.sleep(interval_hours * 3600)
            valid, _ = check_activation()
            if not valid and _on_invalid:
                _on_invalid()
    _license_checker_thread = threading.Thread(target=loop, daemon=True)
    _license_checker_thread.start()

def stop_license_checker():
    global _license_checker_stop
    _license_checker_stop = True


