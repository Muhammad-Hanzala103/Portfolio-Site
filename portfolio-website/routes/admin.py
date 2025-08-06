from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, Project, Skill, Gallery, Testimonial, Service, BlogPost, Contact
from models import SiteVisit

from flask import current_app, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user, login_user, logout_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from app import app, bcrypt, mail

admin_bp = Blueprint('admin', __name__)

# Use current_app to access db lazily inside routes

@admin_bp.route('/dashboard')

@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        db = current_app.extensions['sqlalchemy'].db
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('admin.reset_password', token=token, _external=True)
            # Send email with reset link
            msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
            msg.body = f"To reset your password, visit the following link: {reset_url}\nIf you did not request this, please ignore this email."
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'success')
            return redirect(url_for('admin.admin_login'))
        else:
            flash('Email address not found.', 'danger')
    return render_template('admin/forgot_password.html')

@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # 1 hour expiration
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    except BadSignature:
        flash('Invalid password reset token.', 'danger')
        return redirect(url_for('admin.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin.reset_password', token=token))
        db = current_app.extensions['sqlalchemy'].db
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated. Please log in.', 'success')
            return redirect(url_for('admin.admin_login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('admin.forgot_password'))

    return render_template('admin/reset_password.html', token=token)

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    from app import bcrypt
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = current_app.extensions['sqlalchemy'].db
        user = db.session.query(User).filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=request.form.get('remember') == 'on')
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    db = current_app.extensions['sqlalchemy'].db
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    visits = db.session.query(SiteVisit).filter(SiteVisit.visit_date >= thirty_days_ago).all()
    total_projects = db.session.query(Project).count()
    total_users = db.session.query(User).count()
    total_visits = db.session.query(SiteVisit).count()
    current_year = datetime.now().year
    return render_template('admin/dashboard.html', visits=visits, total_projects=total_projects, total_users=total_users, total_visits=total_visits, current_year=current_year)

@admin_bp.route('/users')
@login_required
def users():
    db = current_app.extensions['sqlalchemy'].db
    users = db.session.query(User).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/projects')
@login_required
def projects():
    db = current_app.extensions['sqlalchemy'].db
    projects = db.session.query(Project).all()
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/skills')
@login_required
def skills():
    db = current_app.extensions['sqlalchemy'].db
    skills = db.session.query(Skill).all()
    return render_template('admin/skills.html', skills=skills)

@admin_bp.route('/gallery')
@login_required
def gallery():
    db = current_app.extensions['sqlalchemy'].db
    gallery_items = db.session.query(Gallery).all()
    return render_template('admin/gallery.html', gallery_items=gallery_items)

@admin_bp.route('/testimonials')
@login_required
def testimonials():
    db = current_app.extensions['sqlalchemy'].db
    testimonials = db.session.query(Testimonial).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@admin_bp.route('/services')
@login_required
def services():
    db = current_app.extensions['sqlalchemy'].db
    services = db.session.query(Service).all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/blog')
@login_required
def blog():
    db = current_app.extensions['sqlalchemy'].db
    blog_posts = db.session.query(BlogPost).all()
    return render_template('admin/blog.html', blog_posts=blog_posts)

@admin_bp.route('/contact')
@login_required
def contact():
    db = current_app.extensions['sqlalchemy'].db
    contacts = db.session.query(Contact).all()
    return render_template('admin/contact.html', contacts=contacts)