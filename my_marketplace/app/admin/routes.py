from flask import render_template, request, flash, redirect, url_for
from . import admin_bp
from models import Dispute, Order
from my_marketplace.app import db

@admin_bp.route('/disputes', methods=['GET', 'POST'])
def manage_disputes():
    if request.method == 'POST':
        dispute_id = request.form.get('dispute_id')
        resolution_notes = request.form.get('resolution_notes')
        action = request.form.get('action')

        dispute = Dispute.query.get_or_404(dispute_id)
        
        if action == 'resolve_in_favor_of_buyer':
            dispute.status = 'resolved'
            dispute.resolution_notes = resolution_notes
            # Refund the buyer
            order = Order.query.get(dispute.order_id)
            order.status = 'refunded'
            db.session.commit()
            flash('Dispute resolved in favor of the buyer and order refunded.', 'success')
        elif action == 'resolve_in_favor_of_seller':
            dispute.status = 'resolved'
            dispute.resolution_notes = resolution_notes
            # Release payment to the seller
            order = Order.query.get(dispute.order_id)
            order.status = 'completed'
            db.session.commit()
            flash('Dispute resolved in favor of the seller and payment released.', 'success')
        else:
            flash('Invalid action.', 'danger')

        return redirect(url_for('admin.manage_disputes'))

    disputes = Dispute.query.all()
    return render_template('disputes.html', disputes=disputes)