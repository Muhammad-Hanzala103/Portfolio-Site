from my_marketplace.app import create_app, db
from my_marketplace.models import User

from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    db.create_all()
    # Create admin user
    admin_user = User.query.filter_by(email='hanzala@gmail.com').first()
    if not admin_user:
        admin_user = User(
            name='Muhammad Hanzala',
            email='hanzala@gmail.com',
            phone='1234567890',
            role='admin',
            email_verified=True
        )
        admin_user.set_password('Hanzala@123')
        db.session.add(admin_user)

    # Create test buyer user
    buyer_user = User.query.filter_by(email='buyer@example.com').first()
    if not buyer_user:
        buyer_user = User(
            name='Test Buyer',
            email='buyer@example.com',
            phone='0987654321',
            role='buyer',
            email_verified=True
        )
        buyer_user.set_password('password')
        db.session.add(buyer_user)

    # Create test seller user
    seller_user = User.query.filter_by(email='seller@example.com').first()
    if not seller_user:
        seller_user = User(
            name='Test Seller',
            email='seller@example.com',
            phone='1122334455',
            role='seller',
            email_verified=True
        )
        seller_user.set_password('password')
        db.session.add(seller_user)

    db.session.commit()

    print('Database seeded!')