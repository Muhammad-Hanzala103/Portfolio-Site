import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User, Gig
from config import TestConfig
from flask import url_for

class AdminGigManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create admin and regular users
        self.admin_user = User(name='admin', email='admin@test.com', password_hash='adminpass', role='admin')
        self.seller_user = User(name='seller', email='seller@test.com', password_hash='sellerpass', role='seller')
        db.session.add_all([self.admin_user, self.seller_user])
        db.session.commit()

        # Create a gig by the seller
        self.gig = Gig(title='Test Gig', slug='test-gig', description='Test Description', category='Test Category', price_basic=10.0, delivery_days_basic=1, seller_id=self.seller_user.id, is_published=False)
        db.session.add(self.gig)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_admin_can_access_manage_gigs_page(self):
        with self.app.test_request_context():
            # Log in as admin
            with self.client.session_transaction() as sess:
                sess['_user_id'] = self.admin_user.id
                sess['_fresh'] = True
            
            response = self.client.get(url_for('admin.manage_gigs'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Manage Gigs', response.data)

    def test_admin_can_approve_gig(self):
        with self.app.test_request_context():
            # Log in as admin
            with self.client.session_transaction() as sess:
                sess['_user_id'] = self.admin_user.id
                sess['_fresh'] = True

            response = self.client.post(url_for('admin.approve_gig', gig_id=self.gig.id), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'has been approved and published', response.data)

            # Verify the gig is published
            gig = Gig.query.get(self.gig.id)
            self.assertTrue(gig.is_published)

if __name__ == '__main__':
    unittest.main()