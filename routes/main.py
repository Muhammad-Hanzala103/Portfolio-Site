from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, copy_current_request_context
from datetime import datetime
import threading
from flask_mail import Message
from utils import generate_sitemap

# Create blueprint first, import models later to avoid circular imports

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Import models and db at runtime to avoid circular imports
    from models import Project, Skill, Testimonial, Service
    from app import db
    
    # Get featured projects for homepage
    # Get featured projects for homepage
    featured_projects = Project.query.filter_by(featured=True).limit(3).all()
    
    # Get skills grouped by category
    skills = Skill.query.all()
    skill_categories = {}
    for skill in skills:
        if skill.category not in skill_categories:
            skill_categories[skill.category] = []
        skill_categories[skill.category].append(skill)
    
    # Get featured testimonials
    testimonials = Testimonial.query.filter_by(featured=True).limit(4).all()
    
    # Get featured services
    services = Service.query.filter_by(featured=True).limit(4).all()

    
    return render_template('index.html', 
                           featured_projects=featured_projects,
                           skill_categories=skill_categories,
                           testimonials=testimonials,
                           services=services)

@main_bp.route('/about')
def about():
    # Import models at runtime to avoid circular imports
    from models import Skill
    from app import db
    
    # Get all skills for about page
    skills = Skill.query.all()
    skill_categories = {}
    for skill in skills:
        if skill.category not in skill_categories:
            skill_categories[skill.category] = []
        skill_categories[skill.category].append(skill)
    
    return render_template('about.html', skill_categories=skill_categories)

@main_bp.route('/projects')
def projects():
    # Import models at runtime to avoid circular imports
    from models import Project
    from app import db
    
    # Get all projects
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

@main_bp.route('/project/<int:project_id>')
def project_detail(project_id):
    # Import models at runtime to avoid circular imports
    from models import Project
    from app import db
    
    # Get specific project
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@main_bp.route('/gallery')
def gallery():
    # Import models at runtime to avoid circular imports
    from models import Gallery
    from app import db
    
    # Get all gallery items
    gallery_items = Gallery.query.order_by(Gallery.created_at.desc()).all()
    
    # Get unique categories for filtering
    from models import GalleryCategory
    categories = db.session.query(GalleryCategory.name).join(Gallery, Gallery.category_id == GalleryCategory.id).distinct().all()
    categories = [category[0] for category in categories if category[0] is not None]
    
    return render_template('gallery.html', gallery_items=gallery_items, categories=categories)

@main_bp.route('/services')
def services():
    # Import models at runtime to avoid circular imports
    from models import Service
    from app import db
    
    # Get all services
    services = Service.query.all()
    return render_template('services.html', services=services)

@main_bp.route('/testimonials')
def testimonials():
    # Import models at runtime to avoid circular imports
    from models import Testimonial
    from app import db
    
    # Get all testimonials
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('testimonials.html', testimonials=testimonials)

@main_bp.route('/blog')
def blog():
    # Import models at runtime to avoid circular imports
    from models import BlogPost
    from app import db
    
    # Get all published blog posts
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=6)
    return render_template('blog.html', posts=posts)

@main_bp.route('/blog/<string:slug>')
def blog_post(slug):
    # Import models at runtime to avoid circular imports
    from models import BlogPost
    from app import db
    
    # Get specific blog post by slug
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    return render_template('blog_post.html', post=post)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Import models at runtime to avoid circular imports
        from models import Contact
        from app import db, mail, app # Import mail and app
        
        # Honeypot spam protection - if this hidden field is filled, it's a bot
        honeypot = request.form.get('website', '')  # Hidden field named 'website'
        if honeypot:
            # Silently reject spam bots
            flash('Your message has been sent!', 'success')  # Fake success
            return redirect(url_for('main.contact'))
        
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Validate form data
        if not name or not email or not subject or not message:
            flash('Please fill out all fields', 'danger')
            return redirect(url_for('main.contact'))
        
        # Create new contact message
        new_message = Contact(name=name, email=email, subject=subject, message=message)
        db.session.add(new_message)
        db.session.commit()

        # Send Email Asynchronously
        msg = Message(subject=f"New Portfolio Contact: {subject}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[app.config['MAIL_USERNAME']])
        msg.body = f"""
        New message from your portfolio:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        """
        
        @copy_current_request_context
        def send_async_email(msg):
            try:
                mail.send(msg)
                print("Email sent successfully!")
            except Exception as e:
                print(f"Failed to send email: {e}")

        email_thread = threading.Thread(target=send_async_email, args=[msg])
        email_thread.start()
        
        flash('Your message has been sent! I will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@main_bp.route('/download-cv')
def download_cv():
    # This would typically serve a static file
    return redirect(url_for('static', filename='files/Muhammad_Hanzala_CV.pdf'))

@main_bp.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap.xml for SEO"""
    from app import app
    xml_content = generate_sitemap(app)
    response = Response(xml_content, mimetype='application/xml')
    return response

@main_bp.route('/robots.txt')
def robots():
    """Generate robots.txt to block admin routes from search engines"""
    robots_txt = '''User-agent: *
Disallow: /admin/
Disallow: /admin_panel/
Disallow: /api/
Disallow: /static/uploads/

Sitemap: {}'''.format(url_for('main.sitemap', _external=True))
    
    response = Response(robots_txt, mimetype='text/plain')
    return response