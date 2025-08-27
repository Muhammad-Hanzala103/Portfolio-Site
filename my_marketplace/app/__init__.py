from flask import Flask
from config import Config
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from my_marketplace.models import User

# Note: We reuse the existing SQLAlchemy instance from the root models.py
from my_marketplace.app.database import db

csrf = CSRFProtect()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO(async_mode='threading')
cors = CORS()
bcrypt = Bcrypt()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # Register user loader for session management
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None
    mail.init_app(app)
    socketio.init_app(app)
    cors.init_app(app)
    bcrypt.init_app(app)
    login_manager.login_view = 'auth.login'

    # Blueprint imports and registration


    from my_marketplace.app.gigs import gigs_bp
    app.register_blueprint(gigs_bp, url_prefix='/gigs')

    from my_marketplace.app.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    from my_marketplace.app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from my_marketplace.app.orders import orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')

    from my_marketplace.app.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')

    from my_marketplace.app.payments import payments_bp
    app.register_blueprint(payments_bp, url_prefix='/payments')

    from my_marketplace.app.webrtc import webrtc_bp
    app.register_blueprint(webrtc_bp, url_prefix='/webrtc')

    from my_marketplace.app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from my_marketplace.app.disputes import disputes_bp
    app.register_blueprint(disputes_bp)

    from routes.main import main_bp
    app.register_blueprint(main_bp)

    from my_marketplace.app.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    

    @app.route('/healthz')
    def healthz():
        return {'status': 'ok'}

    return app