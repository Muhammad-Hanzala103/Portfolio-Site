from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import orders_bp
from models import db, Order, Gig, User, Milestone, Review
import json
from datetime import datetime, timedelta

@orders_bp.route('/my-orders')
@login_required
def my_orders():
    """Display user's orders (both bought and sold)"""
    bought_orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    sold_orders = Order.query.filter_by(seller_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/my_orders.html', bought_orders=bought_orders, sold_orders=sold_orders)

@orders_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Display detailed view of an order with milestones"""
    order = Order.query.get_or_404(order_id)
    
    # Check if user is authorized to view this order
    if current_user.id not in (order.buyer_id, order.seller_id):
        flash('You are not authorized to view this order.', 'error')
        return redirect(url_for('orders.my_orders'))
    
    # Get milestones for this order
    milestones = Milestone.query.filter_by(order_id=order_id).order_by(Milestone.created_at.asc()).all()
    
    return render_template('orders/order_detail.html', order=order, milestones=milestones)

@orders_bp.route('/orders/<int:order_id>/milestones', methods=['POST'])
@login_required
def create_milestone(order_id):
    """Create a new milestone for an order"""
    order = Order.query.get_or_404(order_id)
    
    # Only seller can create milestones
    if current_user.id != order.seller_id:
        return jsonify({'error': 'Only the seller can create milestones'}), 403
    
    # Only allow milestone creation for pending or active orders
    if order.status not in ['pending', 'active']:
        return jsonify({'error': 'Cannot create milestones for this order status'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title')
    description = data.get('description', '')
    amount = data.get('amount')
    due_date = data.get('due_date')
    
    if not title or not amount:
        return jsonify({'error': 'Title and amount are required'}), 400
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400
    
    # Parse due_date if provided
    due_date_obj = None
    if due_date:
        try:
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid due date format. Use YYYY-MM-DD'}), 400
    
    try:
        milestone = Milestone(
            order_id=order_id,
            title=title,
            description=description,
            amount=amount,
            due_date=due_date_obj,
            status='pending'
        )
        db.session.add(milestone)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': milestone.id,
            'title': milestone.title,
            'description': milestone.description,
            'amount': float(milestone.amount),
            'status': milestone.status,
            'due_date': milestone.due_date.isoformat() if milestone.due_date else None,
            'created_at': milestone.created_at.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create milestone: {str(e)}'}), 500

@orders_bp.route('/orders/<int:order_id>/milestones/<int:milestone_id>/complete', methods=['POST'])
@login_required
def complete_milestone(order_id, milestone_id):
    """Mark a milestone as completed"""
    order = Order.query.get_or_404(order_id)
    if current_user.id != order.seller_id:
        return jsonify({'error': 'Only the seller can complete milestones'}), 403
    
    milestone = Milestone.query.filter_by(id=milestone_id, order_id=order_id).first()
    if not milestone:
        return jsonify({'error': 'Milestone not found'}), 404
    
    if milestone.status == 'completed':
        return jsonify({'error': 'Milestone already completed'}), 400
    
    try:
        milestone.status = 'completed'
        milestone.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to complete milestone: {str(e)}'}), 500

@orders_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Update order status with proper validation"""
    order = Order.query.get_or_404(order_id)
    if current_user.id not in [order.buyer_id, order.seller_id] and not current_user.is_admin:
        return jsonify({'error': 'Not authorized'}), 403
    
    new_status = request.json.get('status')
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
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
        return jsonify({'error': f'Invalid status transition from {order.status} to {new_status}'}), 400
    
    # Additional validation based on user role
    if current_user.id == order.buyer_id:
        # Buyers can only mark as completed or disputed
        if new_status not in ['completed', 'disputed']:
            return jsonify({'error': 'Buyers can only mark orders as completed or disputed'}), 403
    elif current_user.id == order.seller_id:
        # Sellers can deliver or cancel
        if new_status not in ['delivered', 'cancelled']:
            return jsonify({'error': 'Sellers can only deliver or cancel orders'}), 403
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/<int:order_id>/reviews', methods=['POST'])
@login_required
def create_review(order_id):
    """Create a review for a completed order"""
    order = Order.query.get_or_404(order_id)

    # 1. Check if the current user is the buyer of the order
    if current_user.id != order.buyer_id:
        return jsonify({'error': 'Only the buyer can review this order.'}), 403

    # 2. Check if the order is completed
    if order.status != 'completed':
        return jsonify({'error': 'You can only review completed orders.'}), 400

    # 3. Check if a review already exists
    existing_review = Review.query.filter_by(order_id=order.id, reviewer_id=current_user.id).first()
    if existing_review:
        return jsonify({'error': 'You have already reviewed this order.'}), 400

    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment')

    if not rating:
        return jsonify({'error': 'Rating is required.'}), 400

    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid rating value.'}), 400

    review = Review(
        order_id=order.id,
        reviewer_id=current_user.id,
        seller_id=order.seller_id,
        rating=rating,
        comment=comment
    )

    try:
        db.session.add(review)
        db.session.commit()
        # Assuming a to_dict() method on the model
        return jsonify({
            'id': review.id,
            'order_id': review.order_id,
            'reviewer_id': review.reviewer_id,
            'seller_id': review.seller_id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to submit review: {str(e)}'}), 500