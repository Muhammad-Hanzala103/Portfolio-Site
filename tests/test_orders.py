import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User, Gig, Order
from config import TestConfig

class OrderTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Create a test buyer and seller
        self.buyer = User(name='buyer', email='buyer@example.com', role='buyer')
        self.seller = User(name='seller', email='seller@example.com', role='seller')
        self.buyer.set_password('password')
        self.seller.set_password('password')
        db.session.add_all([self.buyer, self.seller])
        db.session.commit()
        # Create a test gig
        self.gig = Gig(title='Test Gig', slug='test-gig', description='This is a test gig.', category='testing', price_basic=100, delivery_days_basic=1, seller_id=self.seller.id)
        db.session.add(self.gig)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_order(self):
        # Test creating a new order
        order = Order(buyer_id=self.buyer.id, seller_id=self.seller.id, gig_id=self.gig.id, amount=100, commission=10, status='pending')
        db.session.add(order)
        db.session.commit()
        self.assertIsNotNone(order.id)
        self.assertEqual(order.amount, 100)

if __name__ == '__main__':
    unittest.main()