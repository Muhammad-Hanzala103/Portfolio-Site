from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from datetime import datetime

# Create blueprint first, import models later to avoid circular imports

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Import models and db at runtime to avoid circular imports
    # from my_marketplace.models import Project, Skill, Testimonial, Service
    from my_marketplace.app.database import db
    
    # Get featured projects for homepage
    # featured_projects = Project.query.filter_by(featured=True).limit(3).all()
    featured_projects = []
    
    # Get skills grouped by category
    # skills = Skill.query.all()
    skill_categories = {}
    # for skill in skills:
    #     if skill.category not in skill_categories:
    #         skill_categories[skill.category] = []
    #     skill_categories[skill.category].append(skill)
    
    # Get featured testimonials
    # testimonials = Testimonial.query.filter_by(featured=True).limit(4).all()
    testimonials = []
    
    # Get featured services
    # services = Service.query.filter_by(featured=True).limit(4).all()
    services = []

    
    return render_template('index.html', 
                           featured_projects=featured_projects,
                           skill_categories=skill_categories,
                           testimonials=testimonials,
                           services=services)

@main_bp.route('/about')
def about():
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import Skill
    from my_marketplace.app.database import db
    
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
    from my_marketplace.models import Project
    from my_marketplace.app.database import db
    
    # Get all projects
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

@main_bp.route('/project/<int:project_id>')
def project_detail(project_id):
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import Project
    from my_marketplace.app.database import db
    
    # Get specific project
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@main_bp.route('/gallery')
def gallery():
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import Gallery
    from my_marketplace.app.database import db
    
    # Get all gallery items
    gallery_items = Gallery.query.order_by(Gallery.created_at.desc()).all()
    
    # Get unique categories for filtering
    from my_marketplace.models import GalleryCategory
    categories = db.session.query(GalleryCategory.name).join(Gallery, Gallery.category_id == GalleryCategory.id).distinct().all()
    categories = [category[0] for category in categories if category[0] is not None]
    
    return render_template('gallery.html', gallery_items=gallery_items, categories=categories)

@main_bp.route('/services')
def services():
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import Service
    from my_marketplace.app.database import db
    
    # Get all services
    services = Service.query.all()
    return render_template('services.html', services=services)

@main_bp.route('/testimonials')
def testimonials():
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import Testimonial
    from my_marketplace.app.database import db
    
    # Get all testimonials
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('testimonials.html', testimonials=testimonials)

@main_bp.route('/blog')
def blog():
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import BlogPost
    from my_marketplace.app.database import db
    
    # Get all published blog posts
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=6)
    return render_template('blog.html', posts=posts)

@main_bp.route('/blog/<string:slug>')
def blog_post(slug):
    # Import models at runtime to avoid circular imports
    from my_marketplace.models import BlogPost
    from my_marketplace.app.database import db
    
    # Get specific blog post by slug
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    return render_template('blog_post.html', post=post)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Import models at runtime to avoid circular imports
        from my_marketplace.models import Contact
        from my_marketplace.app.database import db
        
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
    from my_marketplace.models import Project, BlogPost
    
    # Static pages
    pages = [
        {'url': url_for('main.index', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '1.0'},
        {'url': url_for('main.about', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.9'},
        {'url': url_for('main.projects', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.8'},
        {'url': url_for('main.gallery', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.7'},
        {'url': url_for('main.services', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.8'},
        {'url': url_for('main.blog', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.8'},
        {'url': url_for('main.contact', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.7'},
        {'url': url_for('main.testimonials', _external=True), 'lastmod': datetime.now().strftime('%Y-%m-%d'), 'priority': '0.6'},
    ]
    
    # Dynamic project pages
    projects = Project.query.all()
    for project in projects:
        pages.append({
            'url': url_for('main.project_detail', project_id=project.id, _external=True),
            'lastmod': project.updated_at.strftime('%Y-%m-%d') if project.updated_at else datetime.now().strftime('%Y-%m-%d'),
            'priority': '0.6'
        })
    
    # Dynamic blog posts
    blog_posts = BlogPost.query.filter_by(published=True).all()
    for post in blog_posts:
        pages.append({
            'url': url_for('main.blog_post', slug=post.slug, _external=True),
            'lastmod': post.updated_at.strftime('%Y-%m-%d') if post.updated_at else datetime.now().strftime('%Y-%m-%d'),
            'priority': '0.7'
        })
    
    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response = Response(sitemap_xml, mimetype='application/xml')
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