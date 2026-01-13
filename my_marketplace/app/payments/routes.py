import stripe
from flask import request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from . import payments_bp
from my_marketplace.models import Order, Payment, Gig, User, Withdrawal
from ..database import db
from decimal import Decimal

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    data = request.get_json()
    order_id = data.get('order_id')
    order = Order.query.get_or_404(order_id)

    if order.buyer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    gig = Gig.query.get_or_404(order.gig_id)

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Payment for {gig.title}',
                        },
                        'unit_amount': int(order.amount * 100),  # Amount in cents
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=request.host_url + 'orders',
            cancel_url=request.host_url + 'orders',
            metadata={
                'order_id': order.id
            }
        )
        return jsonify({'id': checkout_session.id, 'checkout_url': checkout_session.url})
    except Exception as e:
        return jsonify(error=str(e)), 403

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        
        # Handle wallet top-up
        if metadata.get('type') == 'wallet_topup':
            user_id = metadata.get('user_id')
            amount = Decimal(metadata.get('amount', '0'))
            
            user = User.query.get(user_id)
            if user and amount > 0:
                # Add amount to wallet
                user.wallet_balance += amount
                
                # Create payment record
                payment = Payment(
                    user_id=user.id,
                    order_id=None,  # No order for wallet top-up
                    amount=amount,
                    provider='stripe',
                    status='completed'
                )
                db.session.add(payment)
                db.session.commit()
        
        # Handle order payment
        elif 'order_id' in metadata:
            order_id = metadata['order_id']
            order = Order.query.get(order_id)
            if order and order.status == 'pending':
                order.status = 'active'
                payment = Payment(
                    user_id=order.buyer_id,
                    order_id=order.id,
                    amount=order.amount, # Corrected from order.amount
                    provider='stripe',
                    status='completed'
                )
                db.session.add(payment)
                db.session.commit()

    return 'Success', 200


@payments_bp.route('/checkout')
def checkout():
    return render_template('checkout.html')


@payments_bp.route('/wallet')
@login_required
def wallet():
    """Display user's wallet dashboard"""
    recent_payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(10).all()
    return render_template('payments/wallet.html', recent_payments=recent_payments)


@payments_bp.route('/wallet/topup', methods=['POST'])
@login_required
def create_wallet_topup_session():
    """Create Stripe checkout session for wallet top-up"""
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    if float(amount) < 5.00:  # Minimum top-up amount
        return jsonify({'error': 'Minimum top-up amount is $5.00'}), 400
    
    if float(amount) > 10000.00:  # Maximum top-up amount
        return jsonify({'error': 'Maximum top-up amount is $10,000.00'}), 400

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Wallet Top-up',
                        },
                        'unit_amount': int(float(amount) * 100),  # Amount in cents
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=request.host_url + 'payments/wallet?success=true',
            cancel_url=request.host_url + 'payments/wallet?cancelled=true',
            metadata={
                'type': 'wallet_topup',
                'user_id': current_user.id,
                'amount': str(amount)
            }
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403


@payments_bp.route('/wallet/pay-order', methods=['POST'])
@login_required
def pay_order_with_wallet():
    """Pay for an order using wallet balance"""
    data = request.get_json()
    order_id = data.get('order_id')
    
    if not order_id:
        return jsonify({'error': 'Order ID is required'}), 400
    
    order = Order.query.get_or_404(order_id)
    
    if order.buyer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if order.status != 'pending':
        return jsonify({'error': 'Order cannot be paid'}), 400
    
    # Check if user has sufficient balance
    if current_user.wallet_balance < order.amount:
        return jsonify({'error': 'Insufficient wallet balance'}), 400
    
    try:
        # Deduct amount from wallet
        current_user.wallet_balance -= order.amount
        
        # Update order status
        order.status = 'active'
        
        # Create payment record
        payment = Payment(
            user_id=current_user.id,
            order_id=order.id,
            amount=order.amount,
            provider='wallet',
            status='completed'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment successful',
            'new_balance': float(current_user.wallet_balance)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Payment failed: {str(e)}'}), 500


@payments_bp.route('/api/wallet/balance')
@login_required
def get_wallet_balance():
    """Get current user's wallet balance"""
    return jsonify({
        'balance': float(current_user.wallet_balance),
        'formatted_balance': f'${current_user.wallet_balance:.2f}'
    })


@payments_bp.route('/wallet/withdraw', methods=['GET', 'POST'])
@login_required
def request_withdrawal():
    if request.method == 'POST':
        data = request.get_json()
        amount = data.get('amount')

        if not amount or float(amount) <= 0:
            return jsonify({'error': 'Invalid amount'}), 400

        if current_user.wallet_balance < Decimal(amount):
            return jsonify({'error': 'Insufficient balance'}), 400

        withdrawal = Withdrawal(
            user_id=current_user.id,
            amount=Decimal(amount),
            status='pending'
        )
        db.session.add(withdrawal)
        db.session.commit()

        return jsonify({'message': 'Withdrawal request submitted successfully.'})
    
    return render_template('payments/withdraw.html')