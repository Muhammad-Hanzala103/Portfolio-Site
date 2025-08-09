from app import app, db, bcrypt
from models import User

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        user.username = 'hani'
        user.password = bcrypt.generate_password_hash('hani@62922').decode('utf-8')
        db.session.commit()
        print("Admin user updated!")
    else:
        user = User.query.filter_by(username='hani').first()
        if not user:
            hashed_password = bcrypt.generate_password_hash('hani@62922').decode('utf-8')
            admin = User(username='hani', email='hani75384@gmail.com', password=hashed_password, is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print('Admin user created!')
        else:
            print('Admin user already exists!')