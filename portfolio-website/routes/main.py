from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Project, Skill, Testimonial

# Blueprint for main routes
from flask import Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    projects = Project.query.all()
    skills = Skill.query.all()
    testimonials = Testimonial.query.all()
    return render_template('index.html', projects=projects, skills=skills, testimonials=testimonials)

@login_required
@main_bp.route('/profile')
def profile():
    return render_template('profile.html', user=current_user)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    from models import Contact
    from app import db
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        if not name or not email or not subject or not message:
            flash('Please fill out all fields', 'danger')
            return redirect(url_for('main.contact'))
        new_message = Contact(name=name, email=email, subject=subject, message=message)
        db.session.add(new_message)
        db.session.commit()
        flash('Your message has been sent! I will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    try:
        return render_template('contact.html')
    except Exception:
        flash('Error loading contact page. Please try again later.', 'danger')
        return redirect(url_for('main.index'))