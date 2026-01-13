from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from my_marketplace.models import Order, Review, User, Gig, Milestone
from ..database import db
from .. import csrf
import json
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

# Helper serializers
def order_to_dict(order: Order):
    milestones = []
    if order.milestone_json:
        try:
            milestones = json.loads(order.milestone_json)
        except json.JSONDecodeError:
            milestones = []
    
    return {
        'id': order.id,
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'gig_id': order.gig_id,
        'job_id': order.job_id,
        'amount': float(order.amount),
        'commission': float(order.commission),
        'status': order.status,
        'milestones': milestones,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None,
    }

def review_to_dict(review: Review):
    return {
        'id': review.id,
        'order_id': review.order_id,
        'reviewer_id': review.reviewer_id,
        'seller_id': review.seller_id,
        'rating': review.rating,
        'comment': review.comment,
        'created_at': review.created_at.isoformat() if review.created_at else None,
    }

@orders_bp.get('/ping')
def ping():
    return jsonify(msg='orders ok')

# Order endpoints
@orders_bp.post('/orders')
@login_required
@csrf.exempt
def create_order():
    if current_user.role not in ('buyer', 'both'):
        return jsonify(error='Only buyers can create orders'), 403
    data = request.get_json(silent=True) or {}
    gig_id = data.get('gig_id')
    package_type = data.get('package_type', 'basic')  # basic, standard, premium
    
    if not gig_id:
        return jsonify(error='gig_id is required'), 400
    
    gig = Gig.query.get_or_404(gig_id)
    if gig.seller_id == current_user.id:
        return jsonify(error='Cannot order your own gig'), 400

    # Determine price based on package type
    price_map = {
        'basic': gig.price_basic,
        'standard': gig.price_standard or gig.price_basic,
        'premium': gig.price_premium or gig.price_basic
    }
    
    amount = price_map.get(package_type, gig.price_basic)
    commission = amount * 0.05  # 5% commission

    try:
        order = Order(
            gig_id=gig.id,
            buyer_id=current_user.id,
            seller_id=gig.seller_id,
            amount=amount,
            commission=commission,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        return jsonify(order_to_dict(order)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to create order: {e}'), 500

@orders_bp.get('/orders')
@login_required
def list_orders():
    # Get orders where user is either buyer or seller
    orders = Order.query.filter(
        (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
    ).order_by(Order.created_at.desc()).all()
    
    return jsonify([order_to_dict(o) for o in orders])

@orders_bp.get('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.id not in (order.buyer_id, order.seller_id) and not current_user.is_admin:
        return jsonify(error='Not authorized'), 403
    return jsonify(order_to_dict(order))

@orders_bp.patch('/orders/<int:order_id>')
@login_required
@csrf.exempt
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.id not in (order.buyer_id, order.seller_id) and not current_user.is_admin:
        return jsonify(error='Not authorized'), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify(error='Status is required'), 400

    # Validate status transitions
    valid_transitions = {
        'pending': ['active', 'cancelled'],
        'active': ['delivered', 'disputed', 'cancelled'],
        'delivered': ['completed', 'disputed'],
        'disputed': ['completed', 'cancelled'],
        'completed': [],  # Final state
        'cancelled': []   # Final state
    }
    
    if new_status not in valid_transitions.get(order.status, []):
        return jsonify(error=f'Invalid status transition from {order.status} to {new_status}'), 400
    
    # Additional validation based on user role
    if current_user.id == order.buyer_id:
        # Buyers can only mark as completed or disputed
        if new_status not in ['completed', 'disputed']:
            return jsonify(error='Buyers can only mark orders as completed or disputed'), 403
    elif current_user.id == order.seller_id:
        # Sellers can deliver or cancel
        if new_status not in ['delivered', 'cancelled', 'active']:
            return jsonify(error='Sellers can only activate, deliver or cancel orders'), 403

    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(order_to_dict(order))
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to update order: {e}'), 500

# Reviews endpoints
@orders_bp.post('/orders/<int:order_id>/reviews')
@login_required
@csrf.exempt
def create_review(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.id not in (order.buyer_id, order.seller_id):
        return jsonify(error='Not authorized'), 403

    # Only allow reviews for completed orders
    if order.status != 'completed':
        return jsonify(error='Can only review completed orders'), 400

    # Prevent duplicate review
    existing = Review.query.filter_by(order_id=order_id, reviewer_id=current_user.id).first()
    if existing:
        return jsonify(error='You have already reviewed this order'), 400

    data = request.get_json(silent=True) or {}
    rating = data.get('rating')
    comment = data.get('comment', '')
    if not rating or not (1 <= int(rating) <= 5):
        return jsonify(error='A rating between 1 and 5 is required'), 400

    # Determine who is being reviewed
    seller_id = order.seller_id if current_user.id == order.buyer_id else order.buyer_id
    review = Review(order_id=order_id, reviewer_id=current_user.id, seller_id=seller_id, rating=int(rating), comment=comment)
    try:
        db.session.add(review)
        db.session.commit()
        return jsonify(review_to_dict(review)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to create review: {e}'), 500

@orders_bp.get('/orders/<int:order_id>/reviews')
def list_reviews(order_id):
    reviews = Review.query.filter_by(order_id=order_id).order_by(Review.created_at.desc()).all()
    return jsonify([review_to_dict(r) for r in reviews])

@orders_bp.delete('/reviews/<int:review_id>')
@login_required
@csrf.exempt
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.reviewer_id != current_user.id and not current_user.is_admin:
        return jsonify(error='Not authorized'), 403
    try:
        db.session.delete(review)
        db.session.commit()
        return jsonify(message='Review deleted')
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to delete review: {e}'), 500

# Milestone API endpoints
@orders_bp.post('/orders/<int:order_id>/milestones')
@login_required
@csrf.exempt
def create_milestone_api(order_id):
    """API endpoint to create a milestone"""
    order = Order.query.get_or_404(order_id)
    if current_user.id != order.seller_id and not current_user.is_admin:
        return jsonify(error='Only the seller can create milestones'), 403
    
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    description = data.get('description', '')
    amount = data.get('amount')
    due_date = data.get('due_date')
    
    if not title or not amount or float(amount) <= 0:
        return jsonify(error='Title and valid amount are required'), 400
    
    # Parse existing milestones
    milestones = []
    if order.milestone_json:
        try:
            milestones = json.loads(order.milestone_json)
        except json.JSONDecodeError:
            milestones = []
    
    # Create new milestone
    new_milestone = {
        'id': len(milestones) + 1,
        'title': title,
        'description': description,
        'amount': float(amount),
        'status': 'pending',
        'due_date': due_date,
        'created_at': datetime.utcnow().isoformat(),
        'completed_at': None
    }
    
    milestones.append(new_milestone)
    order.milestone_json = json.dumps(milestones)
    
    try:
        db.session.commit()
        return jsonify(new_milestone), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to create milestone: {e}'), 500

@orders_bp.patch('/orders/<int:order_id>/milestones/<int:milestone_id>')
@login_required
@csrf.exempt
def update_milestone_api(order_id, milestone_id):
    """API endpoint to update a milestone status"""
    order = Order.query.get_or_404(order_id)
    if current_user.id != order.seller_id and not current_user.is_admin:
        return jsonify(error='Only the seller can update milestones'), 403
    
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    
    if new_status not in ['pending', 'completed']:
        return jsonify(error='Status must be pending or completed'), 400
    
    # Parse milestones
    milestones = []
    if order.milestone_json:
        try:
            milestones = json.loads(order.milestone_json)
        except json.JSONDecodeError:
            return jsonify(error='Invalid milestone data'), 400
    
    # Find and update milestone
    milestone_found = False
    for milestone in milestones:
        if milestone['id'] == milestone_id:
            milestone['status'] = new_status
            if new_status == 'completed':
                milestone['completed_at'] = datetime.utcnow().isoformat()
            else:
                milestone['completed_at'] = None
            milestone_found = True
            break
    
    if not milestone_found:
        return jsonify(error='Milestone not found'), 404
    
    order.milestone_json = json.dumps(milestones)
    
    try:
        db.session.commit()
        return jsonify(message='Milestone updated successfully')
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'Failed to update milestone: {e}'), 500

@orders_bp.get('/orders/<int:order_id>/milestones')
@login_required
def get_milestones_api(order_id):
    """API endpoint to get all milestones for an order"""
    order = Order.query.get_or_404(order_id)
    if current_user.id not in (order.buyer_id, order.seller_id) and not current_user.is_admin:
        return jsonify(error='Not authorized'), 403
    
    milestones = []
    if order.milestone_json:
        try:
            milestones = json.loads(order.milestone_json)
        except json.JSONDecodeError:
            milestones = []
    
    return jsonify(milestones)