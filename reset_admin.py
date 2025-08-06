from app import app, db
from models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

with app.app_context():
    # Find admin user
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        # Reset password to 'admin'
        new_password_hash = bcrypt.generate_password_hash('admin').decode('utf-8')
        admin.password = new_password_hash
        db.session.commit()
        print('Admin password reset successfully!')
        
        # Verify the new password
        test_result = bcrypt.check_password_hash(admin.password, 'admin')
        print('Password verification test:', test_result)
    else:
        print('Admin user not found!')