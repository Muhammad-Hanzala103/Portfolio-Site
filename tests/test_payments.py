import unittest
from unittest.mock import patch, MagicMock
from my_marketplace.app import create_app, db
from my_marketplace.models import User, Gig, Order
from config import TestingConfig as TestConfig

class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create test users
        self.seller = User(name='Test Seller', email='seller@example.com', role='seller', email_verified=True)
        self.seller.set_password('password')
        self.buyer = User(name='Test Buyer', email='buyer@example.com', role='buyer', email_verified=True)
        self.buyer.set_password('password')
        db.session.add_all([self.seller, self.buyer])
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

    @patch('stripe.checkout.Session.create')
    def test_purchase_gig(self, mock_stripe_checkout_session_create):
        # 1. Mock Stripe session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.url = 'https://checkout.stripe.com/pay/cs_test_123'
        mock_stripe_checkout_session_create.return_value = mock_session

        # 2. Create a gig as the seller
        gig = Gig(
            title='Test Gig',
            slug='test-gig',
            description='This is a test gig.',
            category='testing',
            price_basic=10.00,
            delivery_days_basic=1,
            seller_id=self.seller.id
        )
        db.session.add(gig)
        db.session.commit()

        # 3. Login as buyer
        response = self.login('buyer@example.com', 'password')
        self.assertEqual(response.status_code, 200)

        # 4. Create an order instance before hitting the checkout
        order = Order(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            gig_id=gig.id,
            amount=gig.price_basic,
            commission=0,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        # 5. Buyer initiates purchase
        with self.client:
            response = self.client.post(
                '/payments/create-checkout-session',
                json={'order_id': order.id}
            )
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsNotNone(data)
            self.assertIn('checkout_url', data)
            self.assertEqual(data['checkout_url'], 'https://checkout.stripe.com/pay/cs_test_123')

        # 6. Simulate successful payment via webhook
        webhook_payload = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'metadata': {
                        'order_id': order.id
                    },
                    'payment_status': 'paid'
                }
            }
        }
        with patch('stripe.Webhook.construct_event') as mock_construct_event:
            mock_construct_event.return_value = webhook_payload
            response = self.client.post('/payments/webhook', json=webhook_payload)
            self.assertEqual(response.status_code, 200)

        # 7. Verify the order status is updated
        updated_order = Order.query.get(order.id)
        self.assertIsNotNone(updated_order)
        self.assertEqual(updated_order.status, 'active')

if __name__ == '__main__':
    unittest.main()