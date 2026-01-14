import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt
from flask_ckeditor import CKEditor
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hani75384@gmail.com'  # Email for website and reset password notifications
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-email-password')
app.config['SITE_LOCATION'] = 'Jhelum, Punjab, Pakistan'  # Updated site location
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://username:password@localhost:5432/portfolio')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Security configurations
app.config['PERMANENT_SESSION_LIFETIME'] = 7200  # 2 hours session timeout
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token timeout
# CSRF protection
# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import db from models to avoid circular imports
from models import db
# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)
ckeditor = CKEditor(app)

cors = CORS(app)
from flask_mail import Mail
from extensions import limiter

mail = Mail(app)
limiter.init_app(app)

# Configure login
login_manager.login_view = 'admin.admin_login'
login_manager.login_message_category = 'info'

# Import models will be done later to avoid circular imports

# Import routes
from routes.main import main_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.payment import payment_bp

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(payment_bp, url_prefix='/payment')

# Stripe Configuration
app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_your_public_key')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_secret_key')
app.config['STRIPE_WEBHOOK_SECRET'] = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')

# Admin panel setup
admin = Admin(app, name='Portfolio Admin', url='/admin_panel', endpoint='admin_panel')

# Secure ModelView that requires authentication
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

# Import models (after db initialization to avoid circular imports)
from models import User
from models import Contact, SiteVisit, Project, Skill, Gallery, Testimonial, Service, BlogPost, FAQ

# Add models to admin
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Project, db.session))
admin.add_view(SecureModelView(Skill, db.session))
admin.add_view(SecureModelView(Gallery, db.session))
admin.add_view(SecureModelView(Testimonial, db.session))
admin.add_view(SecureModelView(Service, db.session))
admin.add_view(SecureModelView(BlogPost, db.session))
admin.add_view(SecureModelView(Contact, db.session))
admin.add_view(SecureModelView(FAQ, db.session))

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # User is imported later, so we need to use the function at runtime
    from models import User
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Track site visits
@app.before_request
def track_visit():
    from models import SiteVisit

    # Force HTTPS in production
    if os.environ.get('FLASK_ENV') == 'production' and not request.is_secure:
        return redirect(request.url.replace('http://', 'https://', 1), code=301)

    # Skip tracking for static files and admin routes
    if request.endpoint and (request.endpoint.startswith('static') or
                           request.endpoint.startswith('admin') or
                           request.endpoint.startswith('admin_panel')):
        return

    # Track the visit
    visit = SiteVisit(
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        page_visited=request.path
    )
    db.session.add(visit)
    db.session.commit()

# Add context processor for templates
@app.context_processor
def inject_now():
    from models import Testimonial
    featured_testimonials = Testimonial.query.filter_by(featured=True).order_by(Testimonial.order_index).all()
    return {'now': datetime.now(), 'featured_testimonials': featured_testimonials}

@app.after_request
def add_cache_headers(response):
    """Add cache headers for static assets"""
    if request.endpoint == 'static':
        # Cache static files for 1 year
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    elif request.endpoint and 'admin' not in request.endpoint:
        # Cache pages for 1 hour
        response.cache_control.max_age = 3600
        response.cache_control.public = True

    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response

# Flask CLI Commands
@app.cli.command('create-admin')
def create_admin():
    """Create an admin user from command line."""
    import click
    from models import User
    
    username = click.prompt('Enter admin username', default='hanzala')
    email = click.prompt('Enter admin email', default='hani75384@gmail.com')
    password = click.prompt('Enter admin password', hide_input=True, confirmation_prompt=True)
    
    # Validate password (simple check for CLI)
    if len(password) < 10:
        click.echo('Error: Password must be at least 10 characters.')
        return
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        click.echo(f'Error: Username {username} already exists.')
        return
    
    if User.query.filter_by(email=email).first():
        click.echo(f'Error: Email {email} already registered.')
        return
    
    # Create admin user
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    admin = User(username=username, email=email, password=hashed_password, is_admin=True)
    db.session.add(admin)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully!')

@app.cli.command('seed')
def seed_database():
    """Seed the database with sample data."""
    from seed import run_seed
    run_seed()
    print('Database seeded successfully!')

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create admin user if none exists (updated credentials per requirements)
        from models import User
        if User.query.count() == 0:
            hashed_password = bcrypt.generate_password_hash('ChangeMe!2025').decode('utf-8')
            admin = User(username='hanzala', email='hani75384@gmail.com', password=hashed_password, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print('Admin user created! Username: hanzala | Password: ChangeMe!2025')
    app.run(debug=True)

