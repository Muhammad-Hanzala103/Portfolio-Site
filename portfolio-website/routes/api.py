from flask import Blueprint, jsonify, request
from models import User, Project, Skill, Gallery, Testimonial, Service, BlogPost, Contact, SiteVisit, db

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@api_bp.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@api_bp.route('/api/skills', methods=['GET'])
def get_skills():
    skills = Skill.query.all()
    return jsonify([skill.to_dict() for skill in skills])

@api_bp.route('/api/gallery', methods=['GET'])
def get_gallery():
    gallery_items = Gallery.query.all()
    return jsonify([item.to_dict() for item in gallery_items])

@api_bp.route('/api/testimonials', methods=['GET'])
def get_testimonials():
    testimonials = Testimonial.query.all()
    return jsonify([testimonial.to_dict() for testimonial in testimonials])

@api_bp.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])

@api_bp.route('/api/blog', methods=['GET'])
def get_blog_posts():
    blog_posts = BlogPost.query.all()
    return jsonify([post.to_dict() for post in blog_posts])

@api_bp.route('/api/contact', methods=['POST'])
def create_contact():
    data = request.get_json()
    new_contact = Contact(**data)
    db.session.add(new_contact)
    db.session.commit()
    return jsonify(new_contact.to_dict()), 201

@api_bp.route('/api/site-visits', methods=['GET'])
def get_site_visits():
    visits = SiteVisit.query.all()
    return jsonify([visit.to_dict() for visit in visits])