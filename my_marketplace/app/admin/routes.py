from flask import render_template, request, flash, redirect, url_for
from . import admin_bp
from my_marketplace.models import User, Gig, Order, Dispute, Event

# @admin_bp.route('/transactions')
# def transactions():
#     transactions = Transaction.query.all()
#     return render_template('transactions.html', transactions=transactions)

@admin_bp.route('/analytics')
def analytics():
    events = Event.query.order_by(Event.timestamp.desc()).all()
    return render_template('events.html', events=events)

@admin_bp.route('/security')
def security():
    return render_template('security.html')
from my_marketplace.app import db

# @admin_bp.route('/flagged-items')
# def flagged_items():
#     items = FlaggedItem.query.all()
#     return render_template('flagged_items.html', items=items)

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

@admin_bp.route('/gigs')
def manage_gigs():
    gigs = Gig.query.all()
    return render_template('admin/gigs.html', gigs=gigs)

@admin_bp.route('/gigs/<int:gig_id>/approve', methods=['POST'])
def approve_gig(gig_id):
    gig = Gig.query.get_or_404(gig_id)
    gig.is_published = True
    db.session.commit()
    flash(f'Gig "{gig.title}" has been approved and published.', 'success')
    return redirect(url_for('admin.manage_gigs'))