from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

# Create blueprint first, import models and db later to avoid circular imports

api_bp = Blueprint('api', __name__)

# API route to get all projects
@api_bp.route('/projects', methods=['GET'])
def get_projects():
    # Import models at runtime to avoid circular imports
    from models import Project, db
    
    projects = Project.query.all()
    result = []
    
    for project in projects:
        result.append({
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'image': project.image,
            'technologies': project.technologies,
            'github_link': project.github_link,
            'live_link': project.live_link,
            'featured': project.featured
        })
    
    return jsonify(result)

# API route to get a specific project
@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    from models import Project, db
    
    project = Project.query.get_or_404(project_id)
    
    result = {
        'id': project.id,
        'title': project.title,
        'description': project.description,
        'image': project.image,
        'technologies': project.technologies,
        'github_link': project.github_link,
        'live_link': project.live_link,
        'featured': project.featured
    }
    
    return jsonify(result)

# API route to get all skills
@api_bp.route('/skills', methods=['GET'])
def get_skills():
    from models import Skill, db
    
    skills = Skill.query.all()
    result = []
    
    for skill in skills:
        result.append({
            'id': skill.id,
            'name': skill.name,
            'proficiency': skill.proficiency,
            'category': skill.category,
            'icon': skill.icon
        })
    
    return jsonify(result)

# API route to get skills by category
@api_bp.route('/skills/<string:category>', methods=['GET'])
def get_skills_by_category(category):
    from models import Skill, db
    
    skills = Skill.query.filter_by(category=category).all()
    result = []
    
    for skill in skills:
        result.append({
            'id': skill.id,
            'name': skill.name,
            'proficiency': skill.proficiency,
            'category': skill.category,
            'icon': skill.icon
        })
    
    return jsonify(result)

# API route to get all gallery items
@api_bp.route('/gallery', methods=['GET'])
def get_gallery():
    from models import Gallery, db
    
    gallery_items = Gallery.query.all()
    result = []
    
    for item in gallery_items:
        result.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'image': item.image,
            'category': item.category
        })
    
    return jsonify(result)

# API route to get gallery items by category
@api_bp.route('/gallery/<string:category>', methods=['GET'])
def get_gallery_by_category(category):
    from models import Gallery, db
    
    gallery_items = Gallery.query.filter_by(category=category).all()
    result = []
    
    for item in gallery_items:
        result.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'image': item.image,
            'category': item.category
        })
    
    return jsonify(result)

# API route to get all testimonials
@api_bp.route('/testimonials', methods=['GET'])
def get_testimonials():
    from models import Testimonial, db
    
    testimonials = Testimonial.query.all()
    result = []
    
    for testimonial in testimonials:
        result.append({
            'id': testimonial.id,
            'client_name': testimonial.client_name,
            'client_position': testimonial.client_position,
            'client_image': testimonial.client_image,
            'rating': testimonial.rating,
            'content': testimonial.content,
            'featured': testimonial.featured
        })
    
    return jsonify(result)

# API route to get all services
@api_bp.route('/services', methods=['GET'])
def get_services():
    from models import Service, db
    
    services = Service.query.all()
    result = []
    
    for service in services:
        result.append({
            'id': service.id,
            'title': service.title,
            'description': service.description,
            'icon': service.icon,
            'featured': service.featured
        })
    
    return jsonify(result)

# API route to get all blog posts
@api_bp.route('/blog', methods=['GET'])
def get_blog_posts():
    from models import BlogPost, db
    
    posts = BlogPost.query.filter_by(published=True).all()
    result = []
    
    for post in posts:
        result.append({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'excerpt': post.excerpt,
            'image': post.image,
            'created_at': post.created_at.strftime('%Y-%m-%d')
        })
    
    return jsonify(result)

# API route to get a specific blog post
@api_bp.route('/blog/<string:slug>', methods=['GET'])
def get_blog_post(slug):
    from models import BlogPost, db
    
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    
    result = {
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'content': post.content,
        'excerpt': post.excerpt,
        'image': post.image,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return jsonify(result)

# API route to submit contact form
@api_bp.route('/contact', methods=['POST'])
def submit_contact():
    from models import Contact, db
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('message'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    new_message = Contact(
        name=data.get('name'),
        email=data.get('email'),
        message=data.get('message')
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Your message has been sent!'})

# API route to get site analytics
@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    from models import SiteVisit, db
    
    # Get visit data for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    visits = SiteVisit.query.filter(SiteVisit.visit_date >= thirty_days_ago).all()
    
    # Process visit data
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
    
    # Convert to lists for JSON response
    dates = []
    counts = []
    for date, count in sorted(visit_dates.items()):
        dates.append(date)
        counts.append(count)
    
    # Sort pages by visit count
    sorted_pages = sorted(visit_pages.items(), key=lambda x: x[1], reverse=True)[:10]
    page_names = [page[0] for page in sorted_pages]
    page_counts = [page[1] for page in sorted_pages]
    
    result = {
        'dates': dates,
        'counts': counts,
        'page_names': page_names,
        'page_counts': page_counts,
        'total_visits': sum(counts)
    }
    
    return jsonify(result)