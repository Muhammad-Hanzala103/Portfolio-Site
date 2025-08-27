from flask import Blueprint, jsonify, request, abort, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os
import uuid

from models import db, Job, Gig, User
from .. import csrf


gigs_bp = Blueprint('gigs', __name__)


@gigs_bp.get('/ping')
def ping():
    return jsonify(msg='gigs ok')


# Helper serializers

def job_to_dict(job: Job):
    return {
        'id': job.id,
        'buyer_id': job.buyer_id,
        'title': job.title,
        'description': job.description,
        'budget_min': job.budget_min,
        'budget_max': job.budget_max,
        'deadline': job.deadline.isoformat() if job.deadline else None,
        'status': job.status,
        'created_at': job.created_at.isoformat() if job.created_at else None,
    }

def gig_to_dict(gig: Gig):
    return {
        'id': gig.id,
        'seller_id': gig.seller_id,
        'title': gig.title,
        'slug': gig.slug,
        'description': gig.description,
        'category': gig.category,
        'tags': gig.tags,
        'price_basic': gig.price_basic,
        'price_standard': gig.price_standard,
        'price_premium': gig.price_premium,
        'delivery_days_basic': gig.delivery_days_basic,
        'delivery_days_standard': gig.delivery_days_standard,
        'delivery_days_premium': gig.delivery_days_premium,
        'revisions_allowed': gig.revisions_allowed,
        'thumbnail_url': gig.thumbnail_url,
        'attachments': gig.attachments,
        'is_published': gig.is_published,
        'created_at': gig.created_at.isoformat() if gig.created_at else None,
    }


# Jobs endpoints

@gigs_bp.post('/jobs')
@login_required
@csrf.exempt
def create_job():
    if current_user.role not in ('buyer', 'both'):
        return jsonify(error='Only buyers can post jobs'), 403
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    budget_min = data.get('budget_min')
    budget_max = data.get('budget_max')
    deadline = data.get('deadline') # Assuming ISO format string
    if not title or not description or budget_min is None or budget_max is None:
        return jsonify(error='title, description, budget_min, and budget_max are required'), 400
    try:
        job = Job(buyer_id=current_user.id, title=title, description=description, budget_min=float(budget_min), budget_max=float(budget_max), deadline=deadline)
        db.session.add(job)
        db.session.commit()
        return jsonify(job_to_dict(job)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to create job: {e}'), 500


@gigs_bp.get('/jobs')
def list_jobs():
    status = request.args.get('status')
    q = Job.query
    if status:
        q = q.filter_by(status=status)
    jobs = q.order_by(Job.created_at.desc()).all()
    return jsonify([job_to_dict(j) for j in jobs])


@gigs_bp.get('/jobs/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify(job_to_dict(job))


@gigs_bp.patch('/jobs/<int:job_id>')
@login_required
@csrf.exempt
def update_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.buyer_id != current_user.id:
        return jsonify(error='Not authorized'), 403
    data = request.get_json(silent=True) or {}
    for field in ('title', 'description', 'budget_min', 'budget_max', 'status', 'deadline'):
        if field in data and data[field] is not None:
            setattr(job, field, data[field])
    try:
        db.session.commit()
        return jsonify(job_to_dict(job))
    except Exception:
        db.session.rollback()
        return jsonify(error='Failed to update job'), 500


@gigs_bp.delete('/jobs/<int:job_id>')
@login_required
@csrf.exempt
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.buyer_id != current_user.id:
        return jsonify(error='Not authorized'), 403
    try:
        db.session.delete(job)
        db.session.commit()
        return jsonify(message='deleted')
    except Exception:
        db.session.rollback()
        return jsonify(error='Failed to delete job'), 500

# Gigs endpoints

@gigs_bp.post('/gigs')
@login_required
@csrf.exempt
def create_gig():
    if current_user.role not in ('seller', 'both'):
        return jsonify(error='Only sellers can create gigs'), 403
    data = request.get_json(silent=True) or {}
    # Basic validation
    required_fields = ['title', 'description', 'category', 'price_basic', 'delivery_days_basic']
    if not all(field in data for field in required_fields):
        return jsonify(error=f'Missing required fields: {required_fields}'), 400

    try:
        gig = Gig(seller_id=current_user.id, **data)
        db.session.add(gig)
        db.session.commit()
        return jsonify(gig_to_dict(gig)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to create gig: {e}'), 500

@gigs_bp.get('/gigs')
def list_gigs():
    gigs = Gig.query.filter_by(is_published=True).order_by(Gig.created_at.desc()).all()
    return jsonify([gig_to_dict(g) for g in gigs])

@gigs_bp.get('/gigs/<int:gig_id>')
def gig_detail(gig_id):
    gig = Gig.query.get_or_404(gig_id)
    return jsonify(gig_to_dict(gig))

@gigs_bp.patch('/gigs/<int:gig_id>')
@login_required
@csrf.exempt
def update_gig(gig_id):
    gig = Gig.query.get_or_404(gig_id)
    if gig.seller_id != current_user.id:
        return jsonify(error='Not authorized'), 403
    data = request.get_json(silent=True) or {}
    for field, value in data.items():
        if hasattr(gig, field):
            setattr(gig, field, value)
    try:
        db.session.commit()
        return jsonify(gig_to_dict(gig))
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to update gig: {e}'), 500

@gigs_bp.delete('/gigs/<int:gig_id>')
@login_required
@csrf.exempt
def delete_gig(gig_id):
    gig = Gig.query.get_or_404(gig_id)
    if gig.seller_id != current_user.id:
        return jsonify(error='Not authorized'), 403
    try:
        db.session.delete(gig)
        db.session.commit()
        return jsonify(message='deleted')
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to delete gig: {e}'), 500


# HTML Routes for Gig Management

@gigs_bp.route('/')
def browse_gigs():
    """Browse all published gigs"""
    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    
    query = Gig.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            db.or_(
                Gig.title.ilike(f'%{search}%'),
                Gig.description.ilike(f'%{search}%'),
                Gig.tags.ilike(f'%{search}%')
            )
        )
    
    gigs = query.order_by(Gig.created_at.desc()).all()
    
    # Get unique categories for filter
    categories = db.session.query(Gig.category).filter_by(is_published=True).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('gigs/browse.html', gigs=gigs, categories=categories, 
                         current_category=category, search_query=search)


@gigs_bp.route('/my-gigs')
@login_required
def my_gigs():
    """Display current user's gigs"""
    if current_user.role not in ('seller', 'both'):
        flash('Only sellers can manage gigs.', 'error')
        return redirect(url_for('gigs.browse_gigs'))
    
    gigs = Gig.query.filter_by(seller_id=current_user.id).order_by(Gig.created_at.desc()).all()
    return render_template('gigs/my_gigs.html', gigs=gigs)


@gigs_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_gig_page():
    """Create a new gig"""
    if current_user.role not in ('seller', 'both'):
        flash('Only sellers can create gigs.', 'error')
        return redirect(url_for('gigs.browse_gigs'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        tags = request.form.get('tags', '').strip()
        
        # Pricing
        price_basic = request.form.get('price_basic')
        price_standard = request.form.get('price_standard')
        price_premium = request.form.get('price_premium')
        
        # Delivery days
        delivery_days_basic = request.form.get('delivery_days_basic')
        delivery_days_standard = request.form.get('delivery_days_standard')
        delivery_days_premium = request.form.get('delivery_days_premium')
        
        revisions_allowed = request.form.get('revisions_allowed', 0)
        is_published = 'is_published' in request.form
        
        # Validation
        if not all([title, description, category, price_basic, delivery_days_basic]):
            flash('Please fill in all required fields.', 'error')
            return render_template('gigs/create.html')
        
        try:
            price_basic = float(price_basic)
            delivery_days_basic = int(delivery_days_basic)
            revisions_allowed = int(revisions_allowed)
            
            if price_standard:
                price_standard = float(price_standard)
            if price_premium:
                price_premium = float(price_premium)
            if delivery_days_standard:
                delivery_days_standard = int(delivery_days_standard)
            if delivery_days_premium:
                delivery_days_premium = int(delivery_days_premium)
                
        except ValueError:
            flash('Please enter valid numbers for prices and delivery days.', 'error')
            return render_template('gigs/create.html')
        
        # Generate slug
        slug = title.lower().replace(' ', '-').replace('_', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Ensure unique slug
        original_slug = slug
        counter = 1
        while Gig.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Handle thumbnail upload
        thumbnail_url = None
        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename:
            filename = secure_filename(thumbnail_file.filename)
            upload_dir = os.path.join('my_marketplace', 'app', 'static', 'uploads', 'gigs')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            thumbnail_file.save(file_path)
            
            thumbnail_url = f"/static/uploads/gigs/{unique_filename}"
        
        try:
            gig = Gig(
                seller_id=current_user.id,
                title=title,
                slug=slug,
                description=description,
                category=category,
                tags=tags,
                price_basic=price_basic,
                price_standard=price_standard,
                price_premium=price_premium,
                delivery_days_basic=delivery_days_basic,
                delivery_days_standard=delivery_days_standard,
                delivery_days_premium=delivery_days_premium,
                revisions_allowed=revisions_allowed,
                thumbnail_url=thumbnail_url,
                is_published=is_published
            )
            
            db.session.add(gig)
            db.session.commit()
            
            flash('Gig created successfully!', 'success')
            return redirect(url_for('gigs.gig_detail_page', slug=gig.slug))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating gig: {str(e)}', 'error')
    
    return render_template('gigs/create.html')


@gigs_bp.route('/<slug>')
def gig_detail_page(slug):
    """View gig details"""
    gig = Gig.query.filter_by(slug=slug).first_or_404()
    
    # Only show published gigs to non-owners
    if not gig.is_published and (not current_user.is_authenticated or gig.seller_id != current_user.id):
        abort(404)
    
    return render_template('gigs/detail.html', gig=gig)


@gigs_bp.route('/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_gig_page(slug):
    """Edit an existing gig"""
    gig = Gig.query.filter_by(slug=slug).first_or_404()
    
    if gig.seller_id != current_user.id:
        flash('You can only edit your own gigs.', 'error')
        return redirect(url_for('gigs.gig_detail_page', slug=slug))
    
    if request.method == 'POST':
        # Update gig with form data (similar to create logic)
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        tags = request.form.get('tags', '').strip()
        
        # Pricing
        price_basic = request.form.get('price_basic')
        price_standard = request.form.get('price_standard')
        price_premium = request.form.get('price_premium')
        
        # Delivery days
        delivery_days_basic = request.form.get('delivery_days_basic')
        delivery_days_standard = request.form.get('delivery_days_standard')
        delivery_days_premium = request.form.get('delivery_days_premium')
        
        revisions_allowed = request.form.get('revisions_allowed', 0)
        is_published = 'is_published' in request.form
        
        # Validation
        if not all([title, description, category, price_basic, delivery_days_basic]):
            flash('Please fill in all required fields.', 'error')
            return render_template('gigs/edit.html', gig=gig)
        
        try:
            gig.title = title
            gig.description = description
            gig.category = category
            gig.tags = tags
            gig.price_basic = float(price_basic)
            gig.price_standard = float(price_standard) if price_standard else None
            gig.price_premium = float(price_premium) if price_premium else None
            gig.delivery_days_basic = int(delivery_days_basic)
            gig.delivery_days_standard = int(delivery_days_standard) if delivery_days_standard else None
            gig.delivery_days_premium = int(delivery_days_premium) if delivery_days_premium else None
            gig.revisions_allowed = int(revisions_allowed)
            gig.is_published = is_published
            
            # Handle thumbnail upload
            thumbnail_file = request.files.get('thumbnail')
            if thumbnail_file and thumbnail_file.filename:
                filename = secure_filename(thumbnail_file.filename)
                upload_dir = os.path.join('my_marketplace', 'app', 'static', 'uploads', 'gigs')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_ext = os.path.splitext(filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_path = os.path.join(upload_dir, unique_filename)
                thumbnail_file.save(file_path)
                
                gig.thumbnail_url = f"/static/uploads/gigs/{unique_filename}"
            
            db.session.commit()
            flash('Gig updated successfully!', 'success')
            return redirect(url_for('gigs.gig_detail_page', slug=gig.slug))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating gig: {str(e)}', 'error')
    
    return render_template('gigs/edit.html', gig=gig)


@gigs_bp.route('/<slug>/delete', methods=['POST'])
@login_required
def delete_gig_page(slug):
    """Delete a gig"""
    gig = Gig.query.filter_by(slug=slug).first_or_404()
    
    if gig.seller_id != current_user.id:
        flash('You can only delete your own gigs.', 'error')
        return redirect(url_for('gigs.gig_detail_page', slug=slug))
    
    try:
        db.session.delete(gig)
        db.session.commit()
        flash('Gig deleted successfully!', 'success')
        return redirect(url_for('gigs.my_gigs'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting gig: {str(e)}', 'error')
        return redirect(url_for('gigs.gig_detail_page', slug=slug))


@gigs_bp.route('/user/<int:user_id>')
def user_gigs(user_id):
    """View all gigs by a specific user"""
    user = User.query.get_or_404(user_id)
    gigs = Gig.query.filter_by(seller_id=user_id, is_published=True).order_by(Gig.created_at.desc()).all()
    return render_template('gigs/user_gigs.html', gigs=gigs, seller=user)


# HTML Routes for Job Management

@gigs_bp.route('/jobs')
def browse_jobs():
    """Browse all active jobs"""
    status = request.args.get('status', 'open')
    search = request.args.get('search', '').strip()
    
    query = Job.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(
            db.or_(
                Job.title.ilike(f'%{search}%'),
                Job.description.ilike(f'%{search}%')
            )
        )
    
    jobs = query.order_by(Job.created_at.desc()).all()
    
    return render_template('jobs/browse.html', jobs=jobs, 
                         current_status=status, search_query=search)


@gigs_bp.route('/jobs/my-jobs')
@login_required
def my_jobs():
    """Display current user's jobs"""
    if current_user.role not in ('buyer', 'both'):
        flash('Only buyers can manage jobs.', 'error')
        return redirect(url_for('gigs.browse_jobs'))
    
    jobs = Job.query.filter_by(buyer_id=current_user.id).order_by(Job.created_at.desc()).all()
    return render_template('jobs/my_jobs.html', jobs=jobs)


@gigs_bp.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def create_job_page():
    """Create a new job"""
    if current_user.role not in ('buyer', 'both'):
        flash('Only buyers can post jobs.', 'error')
        return redirect(url_for('gigs.browse_jobs'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        budget_min = request.form.get('budget_min')
        budget_max = request.form.get('budget_max')
        deadline = request.form.get('deadline')
        
        # Validation
        if not all([title, description, budget_min, budget_max]):
            flash('Please fill in all required fields.', 'error')
            return render_template('jobs/create.html')
        
        try:
            budget_min = float(budget_min)
            budget_max = float(budget_max)
            
            if budget_min < 0 or budget_max < 0:
                flash('Budget amounts must be positive.', 'error')
                return render_template('jobs/create.html')
            
            if budget_min > budget_max:
                flash('Minimum budget cannot be greater than maximum budget.', 'error')
                return render_template('jobs/create.html')
                
        except ValueError:
            flash('Please enter valid numbers for budget amounts.', 'error')
            return render_template('jobs/create.html')
        
        # Parse deadline if provided
        deadline_date = None
        if deadline:
            try:
                from datetime import datetime
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
            except ValueError:
                flash('Please enter a valid deadline date.', 'error')
                return render_template('jobs/create.html')
        
        try:
            job = Job(
                buyer_id=current_user.id,
                title=title,
                description=description,
                budget_min=budget_min,
                budget_max=budget_max,
                deadline=deadline_date,
                status='open'
            )
            
            db.session.add(job)
            db.session.commit()
            
            flash('Job posted successfully!', 'success')
            return redirect(url_for('gigs.job_detail_page', job_id=job.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error posting job: {str(e)}', 'error')
    
    return render_template('jobs/create.html')


@gigs_bp.route('/jobs/<int:job_id>')
def job_detail_page(job_id):
    """View job details"""
    job = Job.query.get_or_404(job_id)
    return render_template('jobs/detail.html', job=job)


@gigs_bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job_page(job_id):
    """Edit an existing job"""
    job = Job.query.get_or_404(job_id)
    
    if job.buyer_id != current_user.id:
        flash('You can only edit your own jobs.', 'error')
        return redirect(url_for('gigs.job_detail_page', job_id=job_id))
    
    if request.method == 'POST':
        # Update job with form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        budget_min = request.form.get('budget_min')
        budget_max = request.form.get('budget_max')
        deadline = request.form.get('deadline')
        status = request.form.get('status', 'open')
        
        # Validation
        if not all([title, description, budget_min, budget_max]):
            flash('Please fill in all required fields.', 'error')
            return render_template('jobs/edit.html', job=job)
        
        try:
            job.title = title
            job.description = description
            job.budget_min = float(budget_min)
            job.budget_max = float(budget_max)
            job.status = status
            
            # Parse deadline if provided
            if deadline:
                from datetime import datetime
                job.deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
            else:
                job.deadline = None
            
            db.session.commit()
            flash('Job updated successfully!', 'success')
            return redirect(url_for('gigs.job_detail_page', job_id=job.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating job: {str(e)}', 'error')
    
    return render_template('jobs/edit.html', job=job)


@gigs_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job_page(job_id):
    """Delete a job"""
    job = Job.query.get_or_404(job_id)
    
    if job.buyer_id != current_user.id:
        flash('You can only delete your own jobs.', 'error')
        return redirect(url_for('gigs.job_detail_page', job_id=job_id))
    
    try:
        db.session.delete(job)
        db.session.commit()
        flash('Job deleted successfully!', 'success')
        return redirect(url_for('gigs.my_jobs'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting job: {str(e)}', 'error')
        return redirect(url_for('gigs.job_detail_page', job_id=job_id))


@gigs_bp.route('/jobs/user/<int:user_id>')
def user_jobs(user_id):
    """View all jobs by a specific user"""
    user = User.query.get_or_404(user_id)
    jobs = Job.query.filter_by(buyer_id=user_id).filter(Job.status != 'closed').order_by(Job.created_at.desc()).all()
    return render_template('jobs/user_jobs.html', jobs=jobs, buyer=user)