import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User, Gig
from config import TestConfig

class GigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Create a test user
        self.user = User(name='testuser', email='test@example.com', role='seller')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_gig(self):
        # Test creating a new gig
        gig = Gig(title='Test Gig', slug='test-gig', description='This is a test gig.', category='testing', price_basic=100, delivery_days_basic=1, seller_id=self.user.id)
        db.session.add(gig)
        db.session.commit()
        self.assertIsNotNone(gig.id)
        self.assertEqual(gig.title, 'Test Gig')

if __name__ == '__main__':
    unittest.main()