import stripe
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import db
from models import Service, ServiceTier, Payment

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json() if request.is_json else request.form
    service_id = data.get('service_id')
    tier_id = data.get('tier_id')
    email = data.get('email')
    
    # Optional fields for custom amounts or donations if needed later
    amount = data.get('amount') 

    domain_url = request.host_url.rstrip('/')
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        line_items = []
        metadata = {
            'customer_email': email
        }

        if service_id:
            service = Service.query.get_or_404(service_id)
            metadata['service_id'] = service.id
            
            price_amount = 0
            product_name = service.title
            description = service.short_description
            
            if tier_id:
                tier = ServiceTier.query.get(tier_id)
                if tier and tier.service_id == service.id:
                    price_amount = int(tier.price * 100) # Cents
                    product_name = f"{service.title} - {tier.name}"
                    description = tier.description
                    metadata['tier_id'] = tier.id
            
            if price_amount == 0 and amount:
                 price_amount = int(float(amount) * 100)

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name,
                        'description': description,
                    },
                    'unit_amount': price_amount,
                },
                'quantity': 1,
            })
        
        else:
            return jsonify({'error': 'Service ID required'}), 400

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=domain_url + url_for('payment.success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + url_for('payment.cancel'),
            customer_email=email,
            metadata=metadata
        )

        return jsonify({'id': checkout_session.id, 'url': checkout_session.url})

    except Exception as e:
        return jsonify({'error': str(e)}), 403

@payment_bp.route('/stripe/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    return 'Success', 200

def handle_checkout_session(session):
    # Check if payment already exists
    existing_payment = Payment.query.filter_by(stripe_session_id=session['id']).first()
    if existing_payment:
        return

    # Create new Payment record
    payment = Payment(
        stripe_session_id=session['id'],
        amount_cents=session['amount_total'],
        currency=session['currency'],
        status=session['payment_status'],
        customer_email=session.get('customer_details', {}).get('email'),
        metadata_json=json.dumps(session.get('metadata', {}))
    )
    
    db.session.add(payment)
    db.session.commit()

@payment_bp.route('/success')
def success():
    return render_template('payment/success.html')

@payment_bp.route('/cancel')
def cancel():
    return render_template('payment/cancel.html')
