# =======================================================
# Al-Khwarizmi University Recruitment Portal
# Designed & Developed by: Omonbayev Jaloliddin
# Telegram: https://t.me/jaloliddin_omonbaev
# =======================================================

import os
import logging
from flask import Flask, redirect, url_for, g, request, jsonify
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

from app.models import db, User, SystemSetting

# Extensions
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
babel = Babel()

# ── Suppress /socket.io/ noise from Werkzeug access log ──────────────────────
class _SocketIOFilter(logging.Filter):
    def filter(self, record):
        return '/socket.io/' not in record.getMessage()

logging.getLogger('werkzeug').addFilter(_SocketIOFilter())
# ─────────────────────────────────────────────────────────────────────────────


def get_locale():
    # Attempt to retrieve language from Flask g context
    if hasattr(g, 'lang_code') and g.lang_code in ['en', 'uz']:
        return g.lang_code
    
    # Fallback: check the request path segments
    path_parts = request.path.split('/')
    if len(path_parts) > 1 and path_parts[1] in ['en', 'uz']:
        return path_parts[1]
        
    return 'en'

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    
    # Initialize Babel with locale selector
    babel.init_app(app, locale_selector=get_locale)
    
    # Register legacy selector if fallback decorator is needed
    try:
        @babel.localeselector
        def legacy_locale_selector():
            return get_locale()
    except AttributeError:
        # Flask-Babel version is newer and doesn't have localeselector decorator
        pass

    # Flask-Login Configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # URL Processors for language routing
    @app.url_defaults
    def add_language_code(endpoint, values):
        if 'lang_code' in values or not g.get('lang_code'):
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values.setdefault('lang_code', g.lang_code)

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        if values is None:
            g.lang_code = 'en'
            return
        g.lang_code = values.pop('lang_code', 'en')
        if g.lang_code not in ['en', 'uz']:
            g.lang_code = 'en'

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp, public_bp
    from app.routes.admin import admin_bp
    from app.routes.hr import hr_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(hr_bp)

    # Redirect root URL to English default
    @app.route('/')
    def index_redirect():
        return redirect(url_for('main.home', lang_code='en'))
        
    # Helper to check if file upload has allowed extensions
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    app.config['ALLOWED_FILE_FUNC'] = allowed_file

    from flask import send_from_directory
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ── Silently handle /socket.io/ requests from browser extensions ──────────
    @app.route('/socket.io/')
    @csrf.exempt
    def socketio_stub():
        return jsonify({}), 200
    # ─────────────────────────────────────────────────────────────────────────

    return app
