from app import app, db
from models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

with app.app_context():
    users = User.query.all()
    print('Total users:', len(users))
    
    for user in users:
        print(f'User: {user.username}, Email: {user.email}, Admin: {user.is_admin}')
    
    print('\nTesting password for admin user:')
    admin = User.query.filter_by(username='admin').first()
    print('Admin found:', admin is not None)
    
    if admin:
        print('Password check result:', bcrypt.check_password_hash(admin.password, 'admin'))
        print('Stored password hash:', admin.password[:50] + '...')
    else:
        print('No admin user found!')