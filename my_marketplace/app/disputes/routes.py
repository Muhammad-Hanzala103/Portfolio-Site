from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from my_marketplace.app import db
from models import Order, Dispute
from . import disputes_bp

@disputes_bp.route('/orders/<int:order_id>/disputes/create', methods=['GET', 'POST'])
@login_required
def create_dispute(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash('You are not authorized to raise a dispute for this order.', 'danger')
        return redirect(url_for('orders.my_orders'))

    if request.method == 'POST':
        reason = request.form.get('reason')
        if not reason:
            flash('Please provide a reason for the dispute.', 'danger')
        else:
            dispute = Dispute(order_id=order.id, raised_by_id=current_user.id, reason=reason)
            order.status = 'disputed'
            db.session.add(dispute)
            db.session.commit()
            flash('Dispute has been raised successfully.', 'success')
            return redirect(url_for('orders.order_details', order_id=order.id))

    return render_template('disputes/create_dispute.html', order=order)

@disputes_bp.route('/disputes/<int:dispute_id>')
@login_required
def view_dispute(dispute_id):
    dispute = Dispute.query.get_or_404(dispute_id)
    if current_user.id not in [dispute.raised_by_id, dispute.order.seller_id] and not current_user.is_admin:
        flash('You are not authorized to view this dispute.', 'danger')
        return redirect(url_for('main.index'))

    return render_template('disputes/view_dispute.html', dispute=dispute)