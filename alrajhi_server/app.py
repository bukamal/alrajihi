from flask import Flask, jsonify
import os
import secrets
from flask_jwt_extended import JWTManager

# flask_limiter اختياري في النسخة المكتبية/المجمعة.
# عند تشغيل التطبيق من PyInstaller قد لا تكون الحزمة مرفقة، ولا يجوز أن يمنع
# ذلك فتح البرنامج أو تشغيل الخادم المحلي. في الإنتاج يفضّل تثبيتها وتفعيلها.
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ModuleNotFoundError:  # pragma: no cover - fallback للتشغيل بدون الاعتماد الاختياري
    def get_remote_address():
        return "127.0.0.1"

    class Limiter:
        def __init__(self, *args, **kwargs):
            self.enabled = False

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def exempt(self, func):
            return func

from alrajhi_server.database.connection import get_db, init_db
import datetime

app = Flask(__name__)

# يجب ضبط ALRAJHI_JWT_SECRET في الإنتاج. fallback للتطوير المحلي فقط.
_jwt_secret = os.environ.get('ALRAJHI_JWT_SECRET')
if not _jwt_secret:
    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ALRAJHI_ENV') == 'production':
        raise RuntimeError('ALRAJHI_JWT_SECRET must be set in production')
    _jwt_secret = secrets.token_urlsafe(64)
app.config['JWT_SECRET_KEY'] = _jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=8)
jwt = JWTManager(app)

limiter = Limiter(get_remote_address, app=app, default_limits=["500 per minute"])

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get('jti')
    if not jti:
        return True
    db = get_db()
    row = db.execute('SELECT 1 FROM token_blacklist WHERE jti = ? LIMIT 1', (jti,)).fetchone()
    return row is not None

init_db()

@app.teardown_appcontext
def close_db(error):
    db = get_db()
    if db:
        db.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'alive', 'app': 'alrajhi_server', 'api_version': 2})

@app.route('/api/routes', methods=['GET'])
def api_routes():
    routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())
    return jsonify({'routes': routes, 'api_version': 2})

# استيراد blueprints
from alrajhi_server.api.auth import auth_bp
from alrajhi_server.api.items import items_bp
from alrajhi_server.api.invoices import invoices_bp
from alrajhi_server.api.customers import customers_bp
from alrajhi_server.api.suppliers import suppliers_bp
from alrajhi_server.api.vouchers import vouchers_bp
from alrajhi_server.api.expenses import expenses_bp
from alrajhi_server.api.manufacturing import manufacturing_bp
from alrajhi_server.api.reports import reports_bp
from alrajhi_server.api.settings import settings_bp
from alrajhi_server.api.users import users_bp
from alrajhi_server.api.audit_log import audit_bp
from alrajhi_server.api.categories import categories_bp
from alrajhi_server.api.returns import returns_bp
from alrajhi_server.api.cashboxes import cashboxes_bp
from alrajhi_server.api.debug import debug_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(items_bp, url_prefix='/api')
app.register_blueprint(invoices_bp, url_prefix='/api')
app.register_blueprint(customers_bp, url_prefix='/api')
app.register_blueprint(suppliers_bp, url_prefix='/api')
app.register_blueprint(vouchers_bp, url_prefix='/api')
app.register_blueprint(expenses_bp, url_prefix='/api')
app.register_blueprint(manufacturing_bp, url_prefix='/api/manufacturing')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(settings_bp, url_prefix='/api')
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(audit_bp, url_prefix='/api')
app.register_blueprint(categories_bp, url_prefix='/api')
app.register_blueprint(returns_bp, url_prefix='/api')
app.register_blueprint(cashboxes_bp, url_prefix='/api')
app.register_blueprint(debug_bp, url_prefix='/api')

if __name__ == '__main__':
    host = os.environ.get('ALRAJHI_HOST', '127.0.0.1')
    port = int(os.environ.get('ALRAJHI_PORT', '8000'))
    debug = os.environ.get('ALRAJHI_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug)


