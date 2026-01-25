from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Project, Skill, Gallery, Testimonial, Service, BlogPost, Contact, SiteVisit, FAQ
from forms import LoginForm, SkillForm, ServiceForm, TestimonialForm, BlogPostForm, GalleryForm, ContactForm, CommentForm, SettingsForm, ProjectForm
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import uuid
import re
import random
import string
from extensions import limiter
from flask_mail import Message

# Create blueprint first, import models and db later to avoid circular imports

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/visits/daily')
@login_required
def api_visits_daily():
    from models import SiteVisit
    from sqlalchemy import func
    
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    # SQLite compatible date grouping
    results = db.session.query(
        func.date(SiteVisit.visit_date).label('date'),
        func.count(SiteVisit.id)
    ).filter(SiteVisit.visit_date >= since)\
     .group_by(func.date(SiteVisit.visit_date))\
     .order_by('date').all()
     
    data = {
        'labels': [r[0] for r in results],
        'values': [r[1] for r in results]
    }
    return jsonify(data)

@admin_bp.route('/api/revenue')
@login_required
def api_revenue():
    from models import Payment
    from sqlalchemy import func
    
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    results = db.session.query(
        func.date(Payment.created_at).label('date'),
        func.sum(Payment.amount_cents)
    ).filter(Payment.created_at >= since, Payment.status == 'paid')\
     .group_by(func.date(Payment.created_at))\
     .order_by('date').all()
     
    data = {
        'labels': [r[0] for r in results],
        'values': [r[1]/100 for r in results] # Convert cents to dollars
    }
    return jsonify(data)

@admin_bp.route('/api/top-pages')
@login_required
def api_top_pages():
    from models import SiteVisit
    from sqlalchemy import func
    
    limit = request.args.get('limit', 10, type=int)
    
    results = db.session.query(
        SiteVisit.page_visited,
        func.count(SiteVisit.id).label('count')
    ).group_by(SiteVisit.page_visited)\
     .order_by(func.count(SiteVisit.id).desc())\
     .limit(limit).all()
     
    data = {
        'labels': [r[0] for r in results],
        'values': [r[1] for r in results]
    }
    return jsonify(data)


# Helper function for file uploads
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add unique identifier to prevent filename collisions
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return f"uploads/{unique_filename}"
    return None

# Create slug from title
def create_slug(title):
    # Import models at runtime to avoid circular imports
    from models import BlogPost
    from app import db
    
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().replace(' ', '-')
    # Remove special characters
    slug = re.sub(r'[^\w-]', '', slug)
    # Ensure uniqueness by adding timestamp if needed
    existing = BlogPost.query.filter_by(slug=slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    return slug

# Password validation helper
def validate_password(password):
    """
    Validate password strength:
    - Minimum 10 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number or special character
    Returns: (bool, str) - (is_valid, error_message)
    """
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[\d!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one number or special character."
    return True, ""

# Admin registration (disabled by default - enable via config)
@admin_bp.route('/register', methods=['GET', 'POST'])
def admin_register():
    from models import User
    from app import db, bcrypt
    
    # Check if registration is enabled (default: disabled for security)
    if not current_app.config.get('ALLOW_REGISTRATION', False):
        flash('Registration is currently disabled.', 'warning')
        return redirect(url_for('admin.admin_login'))
    
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        
        if not email or '@' not in email:
            errors.append("Please enter a valid email address.")
        
        if password != confirm_password:
            errors.append("Passwords do not match.")
        
        # Password strength check
        is_valid, password_error = validate_password(password)
        if not is_valid:
            errors.append(password_error)
        
        # Check uniqueness
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists.")
        
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin/register.html')
        
        # Create user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            is_admin=False  # New registrations are not admins by default
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('admin.admin_login'))
    
    return render_template('admin/register.html')
def send_reset_email(user):
    from flask_mail import Message
    from app import app, mail
    
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    
    reset_url = url_for('admin.reset_password', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending reset email: {e}")
        return False

@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    from models import User
    from app import db
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            if send_reset_email(user):
                flash('An email has been sent with instructions to reset your password.', 'info')
            else:
                flash('There was an issue sending the reset email. Please try again later or contact support.', 'danger')
        else:
            flash('Email address not found.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    return render_template('admin/forgot_password.html')

@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from models import User
    from app import db, bcrypt
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('admin.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Validate password strength
        is_valid, password_error = validate_password(password)
        if not is_valid:
            flash(password_error, 'danger')
            return render_template('admin/reset_password.html')
        
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('admin.admin_login'))
    return render_template('admin/reset_password.html')

# Admin login
@admin_bp.route('/login/google')
def google_login():
    from app import google
    redirect_uri = url_for('admin.google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@admin_bp.route('/authorize')
def google_authorize():
    from app import google, mail, db
    from models import User, VerificationToken
    try:
        token = google.authorize_access_token()
        resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
        email = resp.get('email')
        name = resp.get('name', '')
        google_id = resp.get('sub') # Google's unique subject ID

        # Check if user exists by google_id or email
        user = User.query.filter((User.google_id == google_id) | (User.email == email)).first()
        
        if not user:
            if current_app.config.get('ALLOW_REGISTRATION', False):
                username = email.split('@')[0]
                counter = 1
                base_username = username
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email,
                    full_name=name,
                    google_id=google_id,
                    email_verified=True, # Trusted email from Google
                    is_admin=False
                )
                db.session.add(user)
                db.session.commit()
                
                login_user(user)
                flash('Successfully registered with Google! Please set a password for your account.', 'success')
                return redirect(url_for('admin.set_initial_password'))
            else:
                flash('Registration is currently disabled.', 'danger')
                return redirect(url_for('admin.admin_login'))
        
        # If user exists, update google_id if missing
        if not user.google_id:
            user.google_id = google_id
            db.session.commit()
            
        # Check for 2FA
        if user.two_factor_enabled:
            # Generate 2FA session token
            session['2fa_user_id'] = user.id
            return redirect(url_for('admin.verify_2fa'))
            
        login_user(user)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        print(f"OAuth Error: {e}")
        flash('Failed to authorize with Google.', 'danger')
        return redirect(url_for('admin.admin_login'))

@admin_bp.route('/set-password', methods=['GET', 'POST'])
@login_required
def set_initial_password():
    from app import bcrypt, db
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('admin/set_password.html')
            
        is_valid, error = validate_password(password)
        if not is_valid:
            flash(error, 'danger')
            return render_template('admin/set_password.html')
            
        current_user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
        flash('Profile password set successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/set_password.html')

def send_otp_email(user, code, type_label="Registration"):
    from app import app, mail
    msg = Message(f'{type_label} - Your Verification Code',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    
    msg.body = f'''Your verification code is: {code}
    
This code will expire in 10 minutes. If you did not request this, please ignore this email.
'''
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False

@admin_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    from models import User, VerificationToken
    from app import db
    user_id = session.get('2fa_user_id')
    if not user_id:
        return redirect(url_for('admin.admin_login'))
        
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        code = request.form.get('otp')
        token = VerificationToken.query.filter_by(user_id=user.id, code=code, token_type='2fa').first()
        
        if token and not token.is_expired():
            db.session.delete(token)
            db.session.commit()
            session.pop('2fa_user_id', None)
            login_user(user)
            flash('Two-factor authentication successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid or expired OTP.', 'danger')
            
    # Send OTP if not already sent (simple throttle)
    existing_token = VerificationToken.query.filter_by(user_id=user.id, token_type='2fa').order_by(VerificationToken.created_at.desc()).first()
    if not existing_token or (datetime.utcnow() - existing_token.created_at).total_seconds() > 60:
        code = ''.join(random.choices(string.digits, k=6))
        new_token = VerificationToken(
            user_id=user.id,
            code=code,
            token_type='2fa',
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(new_token)
        db.session.commit()
        send_otp_email(user, code, "Two-Factor Login")
        flash('A verification code has been sent to your email.', 'info')

    return render_template('admin/verify_otp.html', type='2FA')

# Admin login
@admin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    # Import models and extensions at runtime to avoid circular imports
    from models import User
    from app import db, bcrypt
    
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('admin/login.html')

# Admin logout
@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.admin_login'))

# Admin dashboard
@admin_bp.route('/')
@login_required
def dashboard():
    # Import models at runtime to avoid circular imports
    from models import Project, Skill, Gallery, Testimonial, Service, BlogPost, Contact, SiteVisit, ProjectImage
    from app import db
    from datetime import datetime, timedelta
    
    # Count items for dashboard stats
    projects_count = Project.query.count()
    skills_count = Skill.query.count()
    gallery_count = Gallery.query.count()
    testimonials_count = Testimonial.query.count()
    services_count = Service.query.count()
    blog_posts_count = BlogPost.query.count()
    unread_messages_count = Contact.query.filter_by(read=False).count()
    
    # Get recent site visits (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    visits = SiteVisit.query.filter(SiteVisit.visit_date >= week_ago).all()
    
    # Process visit data for chart
    visit_data = {}
    for visit in visits:
        date_str = visit.visit_date.strftime('%Y-%m-%d')
        if date_str in visit_data:
            visit_data[date_str] += 1
        else:
            visit_data[date_str] = 1
    
    # Prepare chart data (last 7 days)
    chart_dates = []
    chart_counts = []
    
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=6-i)
        date_str = date.strftime('%Y-%m-%d')
        chart_dates.append(date.strftime('%m/%d'))
        chart_counts.append(visit_data.get(date_str, 0))
    
    # Get recent messages
    recent_messages = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    
    # Create stats object for template
    stats = {
        'projects': projects_count,
        'skills': skills_count,
        'gallery': gallery_count,
        'testimonials': testimonials_count,
        'services': services_count,
        'blog_posts': blog_posts_count,
        'unread_messages': unread_messages_count
    }
    
    return render_template('admin/dashboard.html',
                          stats=stats,
                          projects_count=projects_count,
                          skills_count=skills_count,
                          gallery_count=gallery_count,
                          testimonials_count=testimonials_count,
                          services_count=services_count,
                          blog_posts_count=blog_posts_count,
                          unread_messages_count=unread_messages_count,
                          visit_dates=chart_dates,
                          visit_counts=chart_counts,
                          recent_messages=recent_messages)

# Projects CRUD
@admin_bp.route('/projects')
@login_required
def projects():
    projects = Project.query.order_by(Project.order_index.asc(), Project.created_at.desc()).all()
    return render_template('admin/projects/index.html', projects=projects)

@admin_bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    from forms import ProjectForm
    from models import ProjectCategory
    
    form = ProjectForm()
    # Load categories dynamically
    categories = ProjectCategory.query.all()
    form.category.choices = [(str(cat.id), cat.name) for cat in categories]
    form.category.choices.insert(0, ('', 'Select Category'))
    
    if form.validate_on_submit():
        # Handle image upload
        image_path = None
        if form.image.data:
            image_path = save_file(form.image.data)
            
        new_project = Project(
            title=form.title.data,
            description=form.description.data,
            short_description=form.short_description.data,
            client=form.client.data,
            role=form.role.data,
            image=image_path,
            github_link=form.github_link.data,
            live_link=form.live_link.data,
            featured=form.featured.data,
            order_index=form.order_index.data or 0,
            category_id=int(form.category.data) if form.category.data else None
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('admin.projects'))
        
    return render_template('admin/projects/new.html', form=form)

@admin_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    from forms import ProjectForm
    from models import ProjectCategory
    
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    
    # Load categories dynamically
    categories = ProjectCategory.query.all()
    form.category.choices = [(str(cat.id), cat.name) for cat in categories]
    form.category.choices.insert(0, ('', 'Select Category'))
    
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.short_description = form.short_description.data
        project.client = form.client.data
        project.role = form.role.data
        project.github_link = form.github_link.data
        project.live_link = form.live_link.data
        project.featured = form.featured.data
        project.order_index = form.order_index.data or 0
        project.category_id = int(form.category.data) if form.category.data else None
        
        if form.image.data:
            project.image = save_file(form.image.data)
            
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin.projects'))
        
    return render_template('admin/projects/edit.html', form=form, project=project)

@admin_bp.route('/projects/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin.projects'))

# Skills CRUD
@admin_bp.route('/skills')
@login_required
def skills():
    skills = Skill.query.all()
    return render_template('admin/skills/index.html', skills=skills)

@admin_bp.route('/skills/new', methods=['GET', 'POST'])
@login_required
def new_skill():
    from forms import SkillForm
    from models import SkillCategory
    from app import db
    
    form = SkillForm()
    
    # Load categories dynamically
    categories = SkillCategory.query.all()
    form.category.choices = [(str(cat.id), cat.name) for cat in categories]
    form.category.choices.insert(0, ('', 'Select Category'))
    
    if form.validate_on_submit():
        # Create new skill
        new_skill = Skill(
            name=form.name.data,
            description=form.description.data,
            proficiency=form.proficiency.data,
            years_experience=form.years_experience.data or 0,
            category_id=int(form.category.data) if form.category.data else None,
            icon=form.icon.data,
            order_index=form.order_index.data or 0
        )
        
        db.session.add(new_skill)
        db.session.commit()
        
        flash('Skill created successfully!', 'success')
        return redirect(url_for('admin.skills'))
    
    return render_template('admin/skills/new.html', form=form)

@admin_bp.route('/skills/edit/<int:skill_id>', methods=['GET', 'POST'])
@login_required
def edit_skill(skill_id):
    from forms import SkillForm
    from models import SkillCategory
    from app import db
    
    skill = Skill.query.get_or_404(skill_id)
    form = SkillForm(obj=skill)
    
    # Load categories dynamically
    categories = SkillCategory.query.all()
    form.category.choices = [(str(cat.id), cat.name) for cat in categories]
    form.category.choices.insert(0, ('', 'Select Category'))
    
    if form.validate_on_submit():
        skill.name = form.name.data
        skill.description = form.description.data
        skill.proficiency = form.proficiency.data
        skill.years_experience = form.years_experience.data or 0
        skill.category_id = int(form.category.data) if form.category.data else None
        skill.icon = form.icon.data
        skill.order_index = form.order_index.data or 0
        
        db.session.commit()
        flash('Skill updated successfully!', 'success')
        return redirect(url_for('admin.skills'))
    
    return render_template('admin/skills/edit.html', skill=skill, form=form)

@admin_bp.route('/skills/delete/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    
    db.session.delete(skill)
    db.session.commit()
    db.session.commit()
    
    flash('Gallery item deleted successfully!', 'success')
    return redirect(url_for('admin.gallery'))

# Testimonials CRUD
@admin_bp.route('/testimonials')
@login_required
def testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@admin_bp.route('/testimonials/new', methods=['GET', 'POST'])
@login_required
def new_testimonial():
    from app import db
    from datetime import datetime
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        client_title = request.form.get('client_title') or request.form.get('client_position')
        rating = request.form.get('rating', type=int) or 5
        content = request.form.get('content')
        platform = request.form.get('platform')
        featured_flag = request.form.get('is_featured') in ['on', 'true', '1'] or ('featured' in request.form)
        order_index = request.form.get('order', type=int) or 0
        date_str = request.form.get('date')

        # Handle image upload
        client_image = None
        if 'client_image' in request.files and request.files['client_image'].filename:
            client_image = save_file(request.files['client_image'])

        # Create new testimonial
        new_item = Testimonial(
            client_name=client_name,
            client_position=client_title,
            client_title=client_title,
            testimonial_text=content,
            platform=platform,
            rating=rating,
            featured=featured_flag,
            order_index=order_index,
            client_image=client_image
        )

        if date_str:
            try:
                new_item.created_at = datetime.strptime(date_str, '%Y-%m-%d')
            except Exception:
                pass

        db.session.add(new_item)
        db.session.commit()

        flash('Testimonial created successfully!', 'success')
        return redirect(url_for('admin.testimonials'))

    return render_template('admin/testimonials/new.html')

@admin_bp.route('/testimonials/edit/<int:testimonial_id>', methods=['GET', 'POST'])
@login_required
def edit_testimonial(testimonial_id):
    from app import db
    from datetime import datetime
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    if request.method == 'POST':
        testimonial.client_name = request.form.get('client_name')
        client_title = request.form.get('client_title') or request.form.get('client_position')
        testimonial.client_position = client_title
        testimonial.client_title = client_title
        testimonial.rating = request.form.get('rating', type=int) or testimonial.rating
        testimonial.testimonial_text = request.form.get('content')
        testimonial.platform = request.form.get('platform')
        testimonial.featured = request.form.get('is_featured') in ['on', 'true', '1'] or ('featured' in request.form)
        testimonial.order_index = request.form.get('order', type=int) or testimonial.order_index

        # Update created_at if date provided
        date_str = request.form.get('date')
        if date_str:
            try:
                testimonial.created_at = datetime.strptime(date_str, '%Y-%m-%d')
            except Exception:
                pass

        # Handle image upload if new image provided
        if 'client_image' in request.files and request.files['client_image'].filename:
            testimonial.client_image = save_file(request.files['client_image'])

        db.session.commit()
        flash('Testimonial updated successfully!', 'success')
        return redirect(url_for('admin.testimonials'))

    return render_template('admin/testimonial_form.html', testimonial=testimonial)

@admin_bp.route('/testimonials/delete/<int:testimonial_id>', methods=['POST'])
@login_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    
    # Delete testimonial image if it exists
    if testimonial.client_image:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], testimonial.client_image.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image: {e}")
    
    db.session.delete(testimonial)
    db.session.commit()
    
    flash('Testimonial deleted successfully!', 'success')
    return redirect(url_for('admin.testimonials'))

# Gallery CRUD
@admin_bp.route('/gallery')
@login_required
def gallery():
    from models import Gallery
    gallery_items = Gallery.query.order_by(Gallery.created_at.desc()).all()
    return render_template('admin/gallery.html', gallery_items=gallery_items)

@admin_bp.route('/gallery/new', methods=['GET', 'POST'])
@login_required
def new_gallery_item():
    from forms import GalleryForm
    from models import Gallery, GalleryCategory
    from app import db
    
    form = GalleryForm()
    # Load categories dynamically
    categories = GalleryCategory.query.all()
    if categories:
        form.category.choices = [(str(cat.id), cat.name) for cat in categories]
    else:
        form.category.choices = [('', 'No Categories Found')]

    if form.validate_on_submit():
        if not categories:
            flash('Please create a gallery category first.', 'warning')
            return render_template('admin/gallery_form.html', form=form)

        image_path = None
        if form.image.data:
            image_path = save_file(form.image.data)
        
        # If image is required but not provided (should be handled by form validator if new)
        if not image_path:
             flash('Image is required for new items.', 'danger')
             return render_template('admin/gallery_form.html', form=form)

        new_item = Gallery(
            title=form.title.data,
            description=form.description.data,
            image=image_path,
            featured=form.featured.data,
            order_index=form.order_index.data or 0,
            category_id=int(form.category.data)
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash('Gallery item created successfully!', 'success')
        return redirect(url_for('admin.gallery'))
        
    return render_template('admin/gallery_form.html', form=form)

@admin_bp.route('/gallery/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_gallery_item(item_id):
    from forms import GalleryForm
    from models import Gallery, GalleryCategory
    from app import db
    
    item = Gallery.query.get_or_404(item_id)
    form = GalleryForm(obj=item)
    
    # Load categories dynamically
    categories = GalleryCategory.query.all()
    if categories:
        form.category.choices = [(str(cat.id), cat.name) for cat in categories]
    else:
        form.category.choices = [('', 'No Categories Found')]
    
    if request.method == 'GET':
        form.category.data = str(item.category_id) if item.category_id else None

    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        item.featured = form.featured.data
        item.order_index = form.order_index.data or 0
        if form.category.data:
             item.category_id = int(form.category.data)
        
        if form.image.data:
            item.image = save_file(form.image.data)
            
        db.session.commit()
        flash('Gallery item updated successfully!', 'success')
        return redirect(url_for('admin.gallery'))
        
    return render_template('admin/gallery_form.html', form=form, item=item)

@admin_bp.route('/gallery/category/add', methods=['POST'])
@login_required
def add_gallery_category():
    from models import GalleryCategory
    from app import db
    
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            category = GalleryCategory(name=name)
            db.session.add(category)
            db.session.commit()
            flash('Gallery category added successfully!', 'success')
        else:
            flash('Category name is required.', 'danger')
            
    return redirect(url_for('admin.gallery'))

@admin_bp.route('/gallery/category/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_gallery_category(category_id):
    from models import GalleryCategory
    from app import db
    
    category = GalleryCategory.query.get_or_404(category_id)
    name = request.form.get('name')
    
    if name:
        category.name = name
        db.session.commit()
        flash('Gallery category updated successfully!', 'success')
    else:
        flash('Category name is required.', 'danger')
        
    return redirect(url_for('admin.gallery'))

@admin_bp.route('/gallery/category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_gallery_category(category_id):
    from models import GalleryCategory
    from app import db
    
    category = GalleryCategory.query.get_or_404(category_id)
    
    # Check if category has items
    if category.gallery_items:
        # Reset items to no category
        for item in category.gallery_items:
            item.category_id = None
            
    db.session.delete(category)
    db.session.commit()
    flash('Gallery category deleted successfully!', 'success')
    return redirect(url_for('admin.gallery'))



@admin_bp.route('/gallery/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_gallery_item(item_id):
    from models import Gallery
    from app import db
    
    item = Gallery.query.get_or_404(item_id)
    
    # Delete image file
    if item.image:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.image.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image: {e}")
            
    db.session.delete(item)
    db.session.commit()
    
    flash('Gallery item deleted successfully!', 'success')
    return redirect(url_for('admin.gallery'))

# Services CRUD
@admin_bp.route('/services')
@login_required
def services():
    services = Service.query.order_by(Service.order_index.asc(), Service.created_at.desc()).all()
    faqs = FAQ.query.all()
    return render_template('admin/services.html', services=services, faqs=faqs)

@admin_bp.route('/services/faq/add', methods=['POST'])
@login_required
def add_faq():
    from app import db
    from models import FAQ
    if request.method == 'POST':
        question = request.form.get('question')
        answer = request.form.get('answer', '')  # Answer is optional
        service_id = request.form.get('service_id')

        if not question or not service_id:
            flash('Question and service ID are required.', 'danger')
            return redirect(url_for('admin.services'))

        faq = FAQ(
            question=question,
            answer=answer,
            service_id=service_id
        )
        db.session.add(faq)
        db.session.commit()
        flash('FAQ added successfully.', 'success')
    return redirect(url_for('admin.services'))

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@login_required
def new_service():
    from app import db
    import json
    if request.method == 'POST':
        title = request.form.get('title')
        short_description = request.form.get('short_description')
        description = request.form.get('description')
        icon = request.form.get('icon')
        order_index = request.form.get('order', type=int) or 0
        featured = request.form.get('is_featured') in ['on', 'true', '1']
        price = request.form.get('price')

        # Features arrays
        feature_icons = request.form.getlist('feature_icons[]')
        feature_descriptions = request.form.getlist('feature_descriptions[]')
        features_list = []
        for i in range(min(len(feature_icons), len(feature_descriptions))):
            if feature_icons[i] or feature_descriptions[i]:
                features_list.append({
                    'icon': feature_icons[i],
                    'description': feature_descriptions[i]
                })

        new_service = Service(
            title=title,
            short_description=short_description,
            description=description,
            icon=icon,
            order_index=order_index,
            featured=featured,
            price=price,
            features=json.dumps(features_list) if features_list else None
        )

        db.session.add(new_service)
        db.session.commit()

        flash('Service created successfully!', 'success')
        return redirect(url_for('admin.services'))

    return render_template('admin/service_form.html')

@admin_bp.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    from app import db
    import json
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        service.title = request.form.get('title')
        service.short_description = request.form.get('short_description')
        service.description = request.form.get('description')
        service.icon = request.form.get('icon')
        service.order_index = request.form.get('order', type=int) or 0
        service.featured = request.form.get('is_featured') in ['on', 'true', '1']
        service.price = request.form.get('price')

        # Features arrays
        feature_icons = request.form.getlist('feature_icons[]')
        feature_descriptions = request.form.getlist('feature_descriptions[]')
        features_list = []
        for i in range(min(len(feature_icons), len(feature_descriptions))):
            if feature_icons[i] or feature_descriptions[i]:
                features_list.append({
                    'icon': feature_icons[i],
                    'description': feature_descriptions[i]
                })
        service.features = json.dumps(features_list) if features_list else None

        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin.services'))

    return render_template('admin/service_form.html', service=service)

@admin_bp.route('/services/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    db.session.delete(service)
    db.session.commit()
    
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('admin.services'))

# Blog Posts CRUD
@admin_bp.route('/blog')
@login_required
def blog_posts():
    from models import BlogPost, BlogCategory, Tag, BlogComment
    
    blog_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    published_count = BlogPost.query.filter_by(published=True).count()
    draft_count = BlogPost.query.filter_by(published=False).count()
    categories = BlogCategory.query.all()
    tags = Tag.query.all()
    comments = BlogComment.query.order_by(BlogComment.created_at.desc()).limit(5).all()
    
    return render_template('admin/blog_posts.html', 
                         blog_posts=blog_posts, 
                         published_count=published_count, 
                         draft_count=draft_count,
                         categories=categories,
                         tags=tags,
                         comments=comments)

@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@login_required
def new_blog_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        published = 'published' in request.form
        
        # Create slug from title
        slug = create_slug(title)
        
        # Handle image upload
        image_path = None
        if 'image' in request.files and request.files['image'].filename:
            image_path = save_file(request.files['image'])
        
        # Create new blog post
        new_post = BlogPost(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            published=published,
            image=image_path
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin.blog_posts'))
    
    form = BlogPostForm()
    return render_template('admin/blog_post_form.html', form=form)

@admin_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.excerpt = request.form.get('excerpt')
        post.published = 'published' in request.form
        
        # Update slug if title changed
        if post.title != request.form.get('title'):
            post.slug = create_slug(request.form.get('title'))
        
        # Handle image upload if new image provided
        if 'image' in request.files and request.files['image'].filename:
            post.image = save_file(request.files['image'])
        
        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.blog_posts'))
    
    return render_template('admin/blog/edit.html', post=post)

@admin_bp.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    # Delete post image if it exists
    if post.image:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.image.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image: {e}")
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin.blog_posts'))

# Contact Messages
@admin_bp.route('/messages')
@login_required
def messages():
    from app import db
    messages = Contact.query.order_by(Contact.created_at.desc()).all()
    unread_count = Contact.query.filter_by(read=False).count()
    return render_template('admin/messages/index.html', messages=messages, unread_count=unread_count)

@admin_bp.route('/messages/<int:message_id>')
@login_required
def view_message(message_id):
    from app import db
    message = Contact.query.get_or_404(message_id)
    
    # Mark as read if not already
    if not message.read:
        message.read = True
        db.session.commit()
    
    return render_template('admin/messages/view.html', message=message)

@admin_bp.route('/messages/delete/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    from app import db
    message = Contact.query.get_or_404(message_id)
    
    db.session.delete(message)
    db.session.commit()
    
    flash('Message deleted successfully!', 'success')
    return redirect(url_for('admin.messages'))

# Profile settings
@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app import bcrypt
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Update username and email
        if username and email:
            current_user.username = username
            current_user.email = email
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            if not bcrypt.check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('admin.profile'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('admin.profile'))
            
            current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('admin.profile'))
    
    return render_template('admin/profile.html')

# Analytics
@admin_bp.route('/analytics')
@login_required
def analytics():
    from models import Contact
    
    # Get date range from request or default to last 30 days
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Parse dates
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Get visit data
    visits = SiteVisit.query.filter(
        SiteVisit.visit_date >= start_datetime,
        SiteVisit.visit_date < end_datetime
    ).all()
    
    # Process visit data for charts
    visit_dates = {}
    visit_pages = {}
    
    for visit in visits:
        # Daily visits
        date_str = visit.visit_date.strftime('%Y-%m-%d')
        if date_str in visit_dates:
            visit_dates[date_str] += 1
        else:
            visit_dates[date_str] = 1
        
        # Page visits
        if visit.page_visited in visit_pages:
            visit_pages[visit.page_visited] += 1
        else:
            visit_pages[visit.page_visited] = 1
    
    # Calculate statistics
    total_visits = len(visits)
    unique_pages = len(visit_pages)
    days_diff = max(1, (end_datetime - start_datetime).days)
    avg_daily_visits = round(total_visits / days_diff, 1)
    
    # Calculate contact rate
    contacts = Contact.query.filter(
        Contact.created_at >= start_datetime,
        Contact.created_at < end_datetime
    ).count()
    contact_rate = round((contacts / max(1, total_visits)) * 100, 1) if total_visits > 0 else 0
    
    # Prepare chart data
    sorted_dates = sorted(visit_dates.keys())
    daily_visits = [visit_dates.get(date, 0) for date in sorted_dates]
    
    # Page analytics
    page_analytics = []
    for page, count in visit_pages.items():
        page_visits = [v for v in visits if v.page_visited == page]
        if page_visits:
            first_visit = min(v.visit_date for v in page_visits)
            last_visit = max(v.visit_date for v in page_visits)
            avg_per_day = count / days_diff
            page_analytics.append({
                'page': page,
                'count': count,
                'first_visit': first_visit,
                'last_visit': last_visit,
                'avg_per_day': avg_per_day
            })
    
    # Sort by most visited pages
    page_analytics.sort(key=lambda x: x['count'], reverse=True)
    sorted_pages = dict(sorted(visit_pages.items(), key=lambda item: item[1], reverse=True)[:10])
    
    # Trends data (weekly aggregation)
    trends = {
        'labels': sorted_dates[-7:] if len(sorted_dates) >= 7 else sorted_dates,
        'data': daily_visits[-7:] if len(daily_visits) >= 7 else daily_visits
    }
    
    # Page distribution data for doughnut chart
    page_distribution = {
        'labels': list(sorted_pages.keys()),
        'data': list(sorted_pages.values())
    }
    
    return render_template('admin/analytics.html',
                          start_date=start_date,
                          end_date=end_date,
                          total_visits=total_visits,
                          unique_pages=unique_pages,
                          avg_daily_visits=avg_daily_visits,
                          contact_rate=contact_rate,
                          visit_dates=sorted_dates,
                          daily_visits=daily_visits,
                          visit_data=visit_dates,
                          page_data=sorted_pages,
                          page_analytics=page_analytics,
                          trends=trends,
                          page_distribution=page_distribution)

# Video Management
@admin_bp.route('/videos')
@login_required
def videos():
    from models import Video
    videos = Video.query.order_by(Video.created_at.desc()).all()
    return render_template('admin/videos.html', videos=videos)

@admin_bp.route('/videos/new', methods=['GET', 'POST'])
@login_required
def new_video():
    from models import Video
    from app import db
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        url = request.form.get('url')
        new_video = Video(title=title, description=description, url=url)
        db.session.add(new_video)
        db.session.commit()
        flash('Video added successfully!', 'success')
        return redirect(url_for('admin.videos'))
    return render_template('admin/video_form.html')

@admin_bp.route('/videos/edit/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    from models import Video
    from app import db
    video = Video.query.get_or_404(video_id)
    if request.method == 'POST':
        video.title = request.form.get('title')
        video.description = request.form.get('description')
        video.url = request.form.get('url')
        db.session.commit()
        flash('Video updated successfully!', 'success')
        return redirect(url_for('admin.videos'))
    return render_template('admin/video_form.html', video=video)

@admin_bp.route('/videos/delete/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    from models import Video
    from app import db
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash('Video deleted successfully!', 'success')
    return redirect(url_for('admin.videos'))

# Skill Category Management
@admin_bp.route('/skills/categories/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_skill_category(category_id):
    from models import SkillCategory
    from app import db
    
    category = SkillCategory.query.get_or_404(category_id)
    category.name = request.form.get('name')
    
    try:
        db.session.commit()
        flash('Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating category.', 'danger')
    
    return redirect(url_for('admin.skills'))

@admin_bp.route('/skills/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_skill_category(category_id):
    from models import SkillCategory, Skill
    from app import db
    
    category = SkillCategory.query.get_or_404(category_id)
    
    # Set skills in this category to have no category
    skills_in_category = Skill.query.filter_by(category_id=category_id).all()
    for skill in skills_in_category:
        skill.category_id = None
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category.', 'danger')
    
    return redirect(url_for('admin.skills'))

# Blog Category Management
@admin_bp.route('/blog/categories/add', methods=['POST'])
@login_required
def add_blog_category():
    from models import BlogCategory
    from app import db
    
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description')
    
    if not slug:
        slug = name.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters
        slug = re.sub(r'[^\w-]', '', slug)
    
    # Check if category already exists
    existing = BlogCategory.query.filter_by(name=name).first()
    if existing:
        flash('Category with this name already exists.', 'danger')
        return redirect(url_for('admin.blog_posts'))
    
    new_category = BlogCategory(
        name=name,
        slug=slug,
        description=description
    )
    
    try:
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding category.', 'danger')
    
    return redirect(url_for('admin.blog_posts'))

@admin_bp.route('/blog/categories/edit/<int:id>', methods=['POST'])
@login_required
def edit_blog_category(id):
    from models import BlogCategory
    from app import db
    
    category = BlogCategory.query.get_or_404(id)
    name = request.form.get('name')
    slug = request.form.get('slug')
    description = request.form.get('description')
    
    if not slug:
        slug = name.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters
        slug = re.sub(r'[^\w-]', '', slug)
    
    # Check if name already exists (excluding current category)
    existing = BlogCategory.query.filter_by(name=name).first()
    if existing and existing.id != id:
        flash('Category with this name already exists.', 'danger')
        return redirect(url_for('admin.blog_posts'))
    
    category.name = name
    category.slug = slug
    category.description = description
    
    try:
        db.session.commit()
        flash('Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating category.', 'danger')
    
    return redirect(url_for('admin.blog_posts'))

@admin_bp.route('/blog/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_blog_category(id):
    from models import BlogCategory, BlogPost
    from app import db
    
    category = BlogCategory.query.get_or_404(id)
    
    # Check if category has posts
    posts_in_category = BlogPost.query.filter_by(category_id=id).count()
    if posts_in_category > 0:
        flash(f'Cannot delete category. It has {posts_in_category} posts associated with it.', 'danger')
        return redirect(url_for('admin.blog_posts'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category.', 'danger')
    
    return redirect(url_for('admin.blog_posts'))

# Blog Tag Management
@admin_bp.route('/blog/tags/add', methods=['POST'])
@login_required
def add_blog_tag():
    from models import Tag
    from app import db
    
    name = request.form.get('name')
    
    if not name:
        flash('Tag name is required.', 'danger')
        return redirect(url_for('admin.blog_posts'))
    
    # Check if tag already exists
    existing = Tag.query.filter_by(name=name).first()
    if existing:
        flash('Tag with this name already exists.', 'danger')
        return redirect(url_for('admin.blog_posts'))
    
    new_tag = Tag(name=name)
    
    try:
        db.session.add(new_tag)
        db.session.commit()
        flash('Tag added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding tag.', 'danger')
    
    return redirect(url_for('admin.blog_posts'))

@admin_bp.route('/blog/tags/delete/<int:id>', methods=['POST'])
@login_required
def delete_blog_tag(id):
    from models import Tag
    from app import db
    
    tag = Tag.query.get_or_404(id)
    
    try:
        db.session.delete(tag)
        db.session.commit()
        flash('Tag deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting tag.', 'danger')
    
    return redirect(url_for('admin.blog_posts'))

# Comments Management
@admin_bp.route('/comments')
@login_required
def comments():
    from models import BlogComment, CommentSettings
    from app import db
    
    # Get all comments with pagination
    page = request.args.get('page', 1, type=int)
    comments = BlogComment.query.order_by(BlogComment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    settings = CommentSettings.query.first()
    if not settings:
        settings = CommentSettings()
        db.session.add(settings)
        db.session.commit()
    
    return render_template('admin/comments.html', comments=comments, settings=settings)

@admin_bp.route('/comments/settings', methods=['POST'])
@login_required
def update_comment_settings():
    from models import CommentSettings
    from app import db
    
    settings = CommentSettings.query.first()
    if not settings:
        settings = CommentSettings()
        db.session.add(settings)
    
    settings.enable_comments = 'enable_comments' in request.form
    settings.moderate_comments = 'moderate_comments' in request.form
    settings.auto_close_after = request.form.get('auto_close_after', type=int)
    
    try:
        db.session.commit()
        flash('Comment settings updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating settings.', 'danger')
    
    return redirect(url_for('admin.comments'))

@admin_bp.route('/site-settings', methods=['GET', 'POST'])
@login_required
def site_settings():
    from models import SiteSettings
    from app import db
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                setting = SiteSettings.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = value
        
        try:
            db.session.commit()
            flash('Site settings updated successfully!', 'success')
            return redirect(url_for('admin.site_settings'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating settings: ' + str(e), 'danger')
            
    settings = SiteSettings.query.order_by(SiteSettings.category).all()
    categories = {}
    for s in settings:
        if s.category not in categories:
            categories[s.category] = []
        categories[s.category].append(s)
        
    return render_template('admin/settings.html', categories=categories)



@admin_bp.route('/comments/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    from models import BlogComment
    from app import db
    
    comment = BlogComment.query.get_or_404(comment_id)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting comment.', 'danger')
    
    return redirect(url_for('admin.comments'))