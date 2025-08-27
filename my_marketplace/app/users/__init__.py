from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from models import db, User
from .. import csrf

users_bp = Blueprint('users', __name__)

@users_bp.get('/ping')
def ping():
    return jsonify(msg='users ok')


@users_bp.get('/me')
@login_required
def me():
    u = current_user
    return jsonify({
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'bio': u.bio,
        'avatar_url': u.avatar_url,
        'location': u.location,
        'languages': u.languages
    })


@users_bp.patch('/me/profile')
@login_required
@csrf.exempt
def update_my_profile():
    u = current_user
    data = request.get_json(silent=True) or {}

    for field in ('bio', 'avatar_url', 'location', 'languages'):
        if field in data:
            setattr(u, field, data[field])
            
    db.session.add(u)
    db.session.commit()
    return jsonify(message='profile updated')


@users_bp.get('/<int:user_id>')
def public_profile(user_id):
    u = User.query.get_or_404(user_id)
    res = {
        'id': u.id,
        'name': u.name,
        'role': u.role,
        'bio': u.bio,
        'avatar_url': u.avatar_url,
        'location': u.location,
        'languages': u.languages
    }
    return jsonify(res)


@users_bp.route('/profile')
@login_required
def profile():
    """Display current user's profile"""
    return render_template('users/profile.html', user=current_user)


@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit current user's profile"""
    if request.method == 'POST':
        # Update basic info
        current_user.name = request.form.get('name', current_user.name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.bio = request.form.get('bio', '')
        current_user.location = request.form.get('location', '')
        current_user.languages = request.form.get('languages', '')
        
        # Handle avatar upload
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join('my_marketplace', 'app', 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file with unique name
            import uuid
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            avatar_file.save(file_path)
            
            # Store relative URL
            current_user.avatar_url = f"/static/uploads/avatars/{unique_filename}"
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('users.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    return render_template('users/edit_profile.html', user=current_user)


@users_bp.route('/profile/<int:user_id>')
def view_profile(user_id):
    """View public profile of any user"""
    user = User.query.get_or_404(user_id)
    return render_template('users/public_profile.html', user=user)

@users_bp.route('/profile/<int:user_id>/reviews')
def user_reviews(user_id):
    """View all reviews for a specific user"""
    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter_by(seller_id=user_id).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    total_reviews = len(reviews)
    average_rating = sum(review.rating for review in reviews) / total_reviews if total_reviews > 0 else 0
    
    return render_template('users/user_reviews.html', 
                         user=user, 
                         reviews=reviews,
                         total_reviews=total_reviews,
                         average_rating=average_rating)