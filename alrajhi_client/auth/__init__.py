from .session import UserSession
from .password import hash_password, verify_password
from .activation import activate, check_activation, start_license_checker, stop_license_checker, activate_network, check_network_activation, activate_feature, check_feature_activation, normalize_feature_activation_id

# دوال الصلاحيات (متوافقة مع التصدير المباشر)
can_manage_production = UserSession.can_manage_production
can_reverse_production = UserSession.can_reverse_production

__all__ = [
    'UserSession', 'hash_password', 'verify_password',
    'activate', 'check_activation', 'start_license_checker', 'stop_license_checker',
    'activate_network', 'check_network_activation', 'activate_feature', 'check_feature_activation', 'normalize_feature_activation_id',
    'can_manage_production', 'can_reverse_production'
]


