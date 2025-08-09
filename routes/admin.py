from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Project, Skill, Gallery, Testimonial, Service, BlogPost, Contact, SiteVisit
from forms import LoginForm, SkillForm, ServiceForm, TestimonialForm, BlogPostForm, GalleryForm, ContactForm, CommentForm, SettingsForm, ProjectForm
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import uuid
import re

# Create blueprint first, import models and db later to avoid circular imports

admin_bp = Blueprint('admin', __name__)

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

# Admin login
@admin_bp.route('/login', methods=['GET', 'POST'])
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
    from models import Project, Skill, Gallery, Testimonial, Service, BlogPost, Contact, SiteVisit
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
    projects = Project.query.all()
    return render_template('admin/projects/index.html', projects=projects)

@admin_bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    from app import db
    
    form = ProjectForm()
    
    if form.validate_on_submit():
        # Handle image upload
        image_path = None
        if form.image.data:
            image_path = save_file(form.image.data)
        
        # Create new project
        new_project = Project(
            title=form.title.data,
            description=form.description.data,
            technologies=form.technologies.data,
            github_link=form.github_url.data,
            live_link=form.live_url.data,
            featured=form.featured.data,
            order_index=form.order_index.data or 0,
            image=image_path
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('admin.projects'))
    
    return render_template('admin/projects/new.html', form=form)

@admin_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.technologies = request.form.get('technologies')
        project.github_link = request.form.get('github_link')
        project.live_link = request.form.get('live_link')
        project.featured = 'featured' in request.form
        
        # Handle image upload if new image provided
        if 'image' in request.files and request.files['image'].filename:
            project.image = save_file(request.files['image'])
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin.projects'))
    
    return render_template('admin/projects/edit.html', project=project)

@admin_bp.route('/projects/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Delete project image if it exists
    if project.image:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], project.image.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image: {e}")
    
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
    
    flash('Skill deleted successfully!', 'success')
    return redirect(url_for('admin.skills'))

# Gallery CRUD
@admin_bp.route('/gallery')
@login_required
def gallery():
    from flask import request
    from models import GalleryCategory
    
    # Base query
    query = Gallery.query

    # Filters
    category_name = request.args.get('category')
    if category_name:
        # Filter by category name via join
        query = query.join(GalleryCategory).filter(GalleryCategory.name == category_name)

    search = request.args.get('search')
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Gallery.title.ilike(like)) | (Gallery.description.ilike(like))
        )

    # Sorting
    sort = request.args.get('sort', 'newest')
    if sort == 'oldest':
        query = query.order_by(Gallery.created_at.asc())
    elif sort == 'title':
        query = query.order_by(Gallery.title.asc())
    elif sort == 'category':
        query = query.join(GalleryCategory).order_by(GalleryCategory.name.asc(), Gallery.created_at.desc())
    else:
        # newest
        query = query.order_by(Gallery.created_at.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Categories for filter UI (if needed in template)
    categories = GalleryCategory.query.all()

    return render_template(
        'admin/gallery/index.html',
        gallery=pagination,
        categories=categories
    )

@admin_bp.route('/gallery/new', methods=['GET', 'POST'])
@login_required
def new_gallery_item():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            image_path = save_file(request.files['image'])
        
        if not image_path:
            flash('Please upload a valid image file', 'danger')
            return redirect(url_for('admin.new_gallery_item'))
        
        # Create new gallery item
        new_item = Gallery(
            title=title,
            description=description,
            category=category,
            image=image_path
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        flash('Gallery item created successfully!', 'success')
        return redirect(url_for('admin.gallery'))
    
    return render_template('admin/gallery/new.html')

@admin_bp.route('/gallery/edit/<int:gallery_id>', methods=['GET', 'POST'])
@login_required
def edit_gallery_item(gallery_id):
    gallery_item = Gallery.query.get_or_404(gallery_id)
    
    if request.method == 'POST':
        gallery_item.title = request.form.get('title')
        gallery_item.description = request.form.get('description')
        gallery_item.category = request.form.get('category')
        
        # Handle image upload if new image provided
        if 'image' in request.files and request.files['image'].filename:
            gallery_item.image = save_file(request.files['image'])
        
        db.session.commit()
        flash('Gallery item updated successfully!', 'success')
        return redirect(url_for('admin.gallery'))
    
    return render_template('admin/gallery/edit.html', gallery_item=gallery_item)

@admin_bp.route('/gallery/delete/<int:gallery_id>', methods=['POST'])
@login_required
def delete_gallery_item(gallery_id):
    gallery_item = Gallery.query.get_or_404(gallery_id)
    
    # Delete gallery image if it exists
    if gallery_item.image:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], gallery_item.image.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image: {e}")
    
    db.session.delete(gallery_item)
    db.session.commit()
    
    flash('Gallery item deleted successfully!', 'success')
    return redirect(url_for('admin.gallery'))

# Testimonials CRUD
@admin_bp.route('/testimonials')
@login_required
def testimonials():
    testimonials = Testimonial.query.all()
    return render_template('admin/testimonials/index.html', testimonials=testimonials)

@admin_bp.route('/testimonials/new', methods=['GET', 'POST'])
@login_required
def new_testimonial():
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        client_position = request.form.get('client_position')
        rating = request.form.get('rating')
        content = request.form.get('content')
        featured = 'featured' in request.form
        
        # Handle image upload
        client_image = None
        if 'client_image' in request.files and request.files['client_image'].filename:
            client_image = save_file(request.files['client_image'])
        
        # Create new testimonial
        new_testimonial = Testimonial(
            client_name=client_name,
            client_position=client_position,
            rating=rating,
            content=content,
            featured=featured,
            client_image=client_image
        )
        
        db.session.add(new_testimonial)
        db.session.commit()
        
        flash('Testimonial created successfully!', 'success')
        return redirect(url_for('admin.testimonials'))
    
    return render_template('admin/testimonials/new.html')

@admin_bp.route('/testimonials/edit/<int:testimonial_id>', methods=['GET', 'POST'])
@login_required
def edit_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    
    if request.method == 'POST':
        testimonial.client_name = request.form.get('client_name')
        testimonial.client_position = request.form.get('client_position')
        testimonial.rating = request.form.get('rating')
        testimonial.content = request.form.get('content')
        testimonial.featured = 'featured' in request.form
        
        # Handle image upload if new image provided
        if 'client_image' in request.files and request.files['client_image'].filename:
            testimonial.client_image = save_file(request.files['client_image'])
        
        db.session.commit()
        flash('Testimonial updated successfully!', 'success')
        return redirect(url_for('admin.testimonials'))
    
    return render_template('admin/testimonials/edit.html', testimonial=testimonial)

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

# Services CRUD
@admin_bp.route('/services')
@login_required
def services():
    services = Service.query.all()
    return render_template('admin/services/index.html', services=services)

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@login_required
def new_service():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        icon = request.form.get('icon')
        featured = 'featured' in request.form
        
        # Create new service
        new_service = Service(
            title=title,
            description=description,
            icon=icon,
            featured=featured
        )
        
        db.session.add(new_service)
        db.session.commit()
        
        flash('Service created successfully!', 'success')
        return redirect(url_for('admin.services'))
    
    return render_template('admin/services/new.html')

@admin_bp.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'POST':
        service.title = request.form.get('title')
        service.description = request.form.get('description')
        service.icon = request.form.get('icon')
        service.featured = 'featured' in request.form
        
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin.services'))
    
    return render_template('admin/services/edit.html', service=service)

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
    blog_posts = BlogPost.query.all()
    published_count = BlogPost.query.filter_by(published=True).count()
    draft_count = BlogPost.query.filter_by(published=False).count()
    return render_template('admin/blog_posts.html', blog_posts=blog_posts, published_count=published_count, draft_count=draft_count)

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
    
    return render_template('admin/blog/new.html')

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
    return render_template('admin/messages/index.html', messages=messages)

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