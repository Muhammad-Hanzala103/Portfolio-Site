import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User
from config import TestingConfig

class AdminTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create test users
        self.admin = User(name='Admin User', email='admin@example.com', role='admin', email_verified=True)
        self.admin.set_password('password')
        self.non_admin = User(name='Non-Admin User', email='user@example.com', role='buyer', email_verified=True)
        self.non_admin.set_password('password')
        db.session.add_all([self.admin, self.non_admin])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def test_admin_access_granted(self):
        """Test that an admin user can access the admin dashboard."""
        with self.client:
            self.login('admin@example.com', 'password')
            response = self.client.get('/admin/settings', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Site Settings', response.data)

    def test_non_admin_access_denied(self):
        """Test that a non-admin user is denied access to the admin dashboard."""
        with self.client:
            self.login('user@example.com', 'password')
            response = self.client.get('/admin/settings', follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            response = self.client.get(response.location)
            self.assertIn(b'You do not have permission to access this page.', response.data)