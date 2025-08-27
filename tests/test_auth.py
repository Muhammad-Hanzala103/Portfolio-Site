import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User
from config import TestConfig

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registration_and_login(self):
        # Test registration
        response = self.client.post('/auth/register', data={
            'name': 'testuser',
            'email': 'test@example.com',
            'phone': '1234567890',
            'password': 'password',
            'confirm_password': 'password',
            'role': 'buyer'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test login
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()