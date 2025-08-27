from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError

from models import db, User
from .. import bcrypt, csrf

auth_bp = Blueprint('auth', __name__)

@auth_bp.get('/ping')
def ping():
    return jsonify(msg='auth ok')


@auth_bp.post('/register')
@csrf.exempt
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone = data.get('phone', '')
    role = (data.get('role') or 'buyer').strip().lower()
    if role not in ('buyer', 'seller', 'both'):
        return jsonify(error='Invalid role'), 400
    if not name or not email or not password or not phone:
        return jsonify(error='name, email, password and phone are required'), 400

    try:
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password_hash=pw_hash, role=role, phone=phone)
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error='email already exists'), 409

    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role), 201


@auth_bp.post('/login')
@csrf.exempt
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify(error='email and password are required'), 400
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify(error='invalid credentials'), 401
    login_user(user)
    return jsonify(message='logged in', user={
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    })


@auth_bp.post('/logout')
@login_required
@csrf.exempt
def logout():
    logout_user()
    return jsonify(message='logged out')