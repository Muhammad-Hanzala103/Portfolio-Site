from flask import request, jsonify
from . import api_bp
from my_marketplace.models import User, Gig, Order

@api_bp.route('/orders', methods=['POST'])
@token_required
def create_order(current_user):
    data = request.get_json()
    gig = Gig.query.get_or_404(data['gig_id'])
    new_order = Order(buyer_id=current_user.id, gig_id=gig.id, seller_id=gig.seller_id)
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'message': 'New order created!', 'order_id': new_order.id})

@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        return jsonify({'message': 'Unauthorized access'}), 403
    return jsonify({
        'id': order.id,
        'buyer_id': order.buyer_id,
        'seller_id': order.seller_id,
        'gig_id': order.gig_id,
        'status': order.status
    })

@api_bp.route('/gigs', methods=['GET'])
@token_required
def get_gigs(current_user):
    gigs = Gig.query.all()
    return jsonify([{'id': gig.id, 'title': gig.title, 'description': gig.description} for gig in gigs])

@api_bp.route('/gigs', methods=['POST'])
@token_required
def create_gig(current_user):
    data = request.get_json()
    new_gig = Gig(title=data['title'], description=data['description'], seller_id=current_user.id)
    db.session.add(new_gig)
    db.session.commit()
    return jsonify({'message': 'New gig created!'})
from my_marketplace.app import db, bcrypt
import jwt
import datetime
from functools import wraps
from flask import current_app

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@api_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'New user created!'})

@api_bp.route('/auth/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
    user = User.query.filter_by(username=auth.username).first()
    if not user:
        return jsonify({'message': 'Could not verify'}), 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
    if bcrypt.check_password_hash(user.password, auth.password):
        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, current_app.config['SECRET_KEY'])
        @api_bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'username': user.username,
        'email': user.email
    })
    return jsonify({'message': 'Could not verify'}), 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}