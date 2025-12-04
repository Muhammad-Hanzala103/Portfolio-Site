import stripe
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/booking/<int:service_id>', methods=['GET'])
def booking_details(service_id):
    from models import Service, ServiceTier
    service = Service.query.get_or_404(service_id)
    tier_id = request.args.get('tier_id')
    selected_tier = None
    if tier_id:
        selected_tier = ServiceTier.query.get(tier_id)
        
    return render_template('booking_details.html', service=service, selected_tier=selected_tier)

@payment_bp.route('/process-booking/<int:service_id>', methods=['POST'])
def process_booking(service_id):
    from models import Service, Order, ServiceTier
    from app import db
    
    service = Service.query.get_or_404(service_id)
    
    # Get form data
    email = request.form.get('email')
    deadline = request.form.get('deadline')
    project_details = request.form.get('project_details')
    tier_id = request.form.get('tier_id')
    
    tier = None
    price = 1000 # Default fallback
    description = service.short_description
    
    if tier_id:
        tier = ServiceTier.query.get(tier_id)
        if tier:
            price = int(tier.price * 100)
            description = f"{tier.name} Package: {tier.description}"
    
    domain_url = request.host_url.rstrip('/')
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"{service.title} ({tier.name if tier else 'Custom'})",
                        'description': description,
                        'images': [domain_url + url_for('static', filename=service.icon)] if service.icon and not service.icon.startswith('fa') else [],
                    },
                    'unit_amount': price,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain_url + url_for('payment.success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + url_for('payment.cancel'),
            metadata={
                'service_id': service.id,
                'tier_id': tier.id if tier else '',
                'customer_email': email,
                'deadline': deadline,
                'project_details': project_details[:500] # Truncate for metadata limit
            }
        )
        
        # Create pending order in DB
        order = Order(
            stripe_session_id=checkout_session.id,
            amount=checkout_session.amount_total / 100,
            currency=checkout_session.currency,
            status='pending',
            customer_email=email,
            service_id=service.id,
            tier_name=tier.name if tier else 'Custom',
            project_details=project_details,
            deadline=deadline
        )
        db.session.add(order)
        db.session.commit()

        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)

@payment_bp.route('/payment/success')
def success():
    from models import Order
    session_id = request.args.get('session_id')
    if session_id:
        order = Order.query.filter_by(stripe_session_id=session_id).first()
        return render_template('payment/success.html', order=order)
    return render_template('payment/success.html')

@payment_bp.route('/payment/cancel')
def cancel():
    return render_template('payment/cancel.html')

@payment_bp.route('/webhook', methods=['POST'])
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
    from models import Order
    from app import db
    
    order = Order.query.filter_by(stripe_session_id=session['id']).first()
    if order:
        order.status = 'paid'
        # If order wasn't created before (e.g. direct link), create it now
        if not order.customer_email:
             order.customer_email = session.get('customer_details', {}).get('email')
        
        db.session.commit()
