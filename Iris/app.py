import os
import __main__
from flask import Flask, request, render_template_string

from core.config import Config
from datetime import datetime, UTC
import time
from models.database import db, init_db, User, LogSocket
from views.api_views import api_bp
from views.admin_views import admin_bp
from views.views import route_bp
from core.protect import Fail2Ban
from core.error import error_404
from core.logging import CustomWerkzeugLogHandler
from core.fabric import refresh_db # Import refresh_db
import logging
import zpp_store
    

class Backend():
    def __init__(self):
        self.notification_queue = []
        self.whitelist_page = ["/.well-known/appspecific/com.chrome.devtools.json"]
        self.app_settings = Config('settings.yaml').get()
        self.app_settings = zpp_store.structure(self.app_settings)

        template_dir = os.path.abspath(self.app_settings.get("server.template_dir", "templates"))
        static_dir = os.path.abspath(self.app_settings.get("server.static_dir", "static"))

        """Application Factory"""
        self.app = Flask("Iris", template_folder=template_dir, static_folder=static_dir, instance_relative_config=True)

        self.auth_required = self.app_settings.get("app.auth", False)
        self.admin_enable = self.app_settings.get("app.admin", False)
        self.home_enable = self.app_settings.get("app.home", False)
        
        # Register Blueprints
        self.app.register_blueprint(api_bp)

        if self.home_enable:
            self.app.register_blueprint(route_bp)

        if self.admin_enable:
            self.app.register_blueprint(admin_bp)

        try:
            os.makedirs(self.app.instance_path)
        except OSError:
            pass

        self.db_file = self.app_settings.get("database.filename", False)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(self.app.instance_path, self.db_file)}'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        init_db(self.app)

        # Register request logging hooks
        self.app.before_request(self._before_request_log)
        self.app.after_request(self._after_request_log)

    def _before_request_log(self):
        request.start_time = time.time()
        # Capture request body. This might consume the stream for the main handler
        # if it also tries to read the raw data. For form/json data, it's usually fine.
        
        # Exclude sensitive data from request_body for login and other sensitive paths
        sensitive_paths = ['/admin/login', '/login'] # Add other sensitive paths if necessary
        if request.path in sensitive_paths:
            request.logged_request_body = "[SENSITIVE_DATA_OMITTED]"
        else:
            request.logged_request_body = request.get_data(as_text=True)

    def _after_request_log(self, response):
        try:
            response_time_ms = int((time.time() - request.start_time) * 1000)
            log_entry = LogSocket(
                timestamp=datetime.now(UTC),
                ip_address=request.remote_addr,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                request_body=getattr(request, 'logged_request_body', None) # Safely retrieve
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            # Log the error to console or a file, but don't break the request
            print(f"Error logging request: {e}")
            db.session.rollback() # Rollback in case of error

        return response

    def run_settings(self):
        self.server_address = self.app_settings.get('server.host', '127.0.0.1')
        self.port = self.app_settings.get('server.port', 4444)

        self.app.config['SECRET_KEY'] = self.app_settings.get("secret_key", None)

        self.app_mode = self.app_settings.get("app.mode", "DEV")
        self.debug = self.app_settings.get("app.debug", False)

        ## CONFIGURATION FAIL2BAN ##
        self.enable_auto_protect = self.app_settings.get("auto_protect.enable", False)

        if self.enable_auto_protect:
            blacklist = self.app_settings.get("auto_protect.blacklist", [])
            whitelist = self.app_settings.get("auto_protect.whitelist", [])
            max_fail = self.app_settings.get("auto_protect.max_fail", 5)
            fail_interval = self.app_settings.get("auto_protect.fail_interval", 300)
            ban_time = self.app_settings.get("auto_protect.ban_time", 300)

            self.protect = Fail2Ban(self.app, blacklist, whitelist, max_fail, fail_interval, ban_time)
        ## CONFIGURATION FAIL2BAN ##
        
        #self.register_error_handlers()
        self.app.errorhandler(404)(self.page_not_found)
        self.app.errorhandler(500)(self.internal_server_error)


    def page_not_found(self, *args):
        if self.enable_auto_protect and request.path not in self.whitelist_page:
            response = self.protect.auto_protect()
            if response:
                return response

        return render_template_string(error_404()), 404


    def internal_server_error(self, *args):
        if self.enable_auto_protect and request.path not in self.whitelist_page:
            response = self.protect.auto_protect()
            if response:
                return response

        return render_template_string(error_404()), 500

    def setup_handler_logs(self):
        # Configure Werkzeug logger for custom access log format
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.INFO) # Set to INFO or DEBUG as needed

        # Remove existing handlers to prevent duplicate output
        for handler in list(werkzeug_logger.handlers):
            werkzeug_logger.removeHandler(handler)

        # Add our custom handler
        werkzeug_logger.addHandler(CustomWerkzeugLogHandler())


    def run_server(self):
        # Ajoute ProxyFix
        from werkzeug.middleware.proxy_fix import ProxyFix
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_host=1)

        if self.app_mode == "PROD":
            serve(self.app, host=self.server_address, port=self.port)
        else:
            self.app.run(host=self.server_address, port=self.port, debug=True)


if __name__ == '__main__':
    # Initialiser les variables globales attendues par votre module d'authentification
    __main__.auth_cache = {}
    __main__.backend = Backend()

    with  __main__.backend.app.app_context():
        __main__.backend.run_settings()
        __main__.backend.setup_handler_logs()

        # Créer un utilisateur admin par défaut si aucun n'existe
        if not User.query.filter_by(username='admin').first():
            print("No admin user found. Creating a default one.")
            admin_user = User(username='admin', role='admin')
            password = 'password'
            admin_user.set_password(password) # Changez ceci dans un environnement de production !
            db.session.add(admin_user)
            db.session.commit()
            print(f"User '{admin_user.username}' created with password '{password}'.")

        # Créer un utilisateur standard par défaut si aucun n'existe
        if not User.query.filter_by(username='user').first():
            print("No standard user found. Creating a default one.")
            standard_user = User(username='user', role='user')
            password = 'password'
            standard_user.set_password(password) # Changez ceci dans un environnement de production !
            db.session.add(standard_user)
            db.session.commit()
            print(f"User '{standard_user.username}' created with password '{password}'.")

    __main__.backend.run_server()


