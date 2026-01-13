import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User, Withdrawal
from decimal import Decimal

class TestWithdrawal(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a user and log in
        self.user = User(name='testuser', email='test@example.com', role='buyer', wallet_balance=Decimal('100.00'))
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = self.user.id
                sess['_fresh'] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_request_withdrawal(self):
        with self.app.test_request_context():
            response = self.client.post('/payments/wallet/withdraw', json={'amount': '50.00'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], 'Withdrawal request submitted successfully.')

            withdrawal = Withdrawal.query.filter_by(user_id=self.user.id).first()
            self.assertIsNotNone(withdrawal)
            self.assertEqual(withdrawal.amount, Decimal('50.00'))
            self.assertEqual(withdrawal.status, 'pending')

    def test_approve_withdrawal(self):
        withdrawal = Withdrawal(user_id=self.user.id, amount=Decimal('50.00'), status='pending')
        db.session.add(withdrawal)
        db.session.commit()

        admin = User(name='admin', email='admin@example.com', role='admin')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = admin.id
                sess['_fresh'] = True
        
        with self.app.test_request_context():
            response = self.client.post(f'/admin/withdrawals/{withdrawal.id}/approve')
            self.assertEqual(response.status_code, 302)

            updated_withdrawal = Withdrawal.query.get(withdrawal.id)
            self.assertEqual(updated_withdrawal.status, 'approved')

            user = User.query.get(self.user.id)
            self.assertEqual(user.wallet_balance, Decimal('50.00'))

    def test_reject_withdrawal(self):
        withdrawal = Withdrawal(user_id=self.user.id, amount=Decimal('50.00'), status='pending')
        db.session.add(withdrawal)
        db.session.commit()

        admin = User(name='admin', email='admin@example.com', role='admin')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['_user_id'] = admin.id
                sess['_fresh'] = True

        with self.app.test_request_context():
            response = self.client.post(f'/admin/withdrawals/{withdrawal.id}/reject')
            self.assertEqual(response.status_code, 302)

            updated_withdrawal = Withdrawal.query.get(withdrawal.id)
            self.assertEqual(updated_withdrawal.status, 'rejected')

            user = User.query.get(self.user.id)
            self.assertEqual(user.wallet_balance, Decimal('100.00'))

if __name__ == '__main__':
    unittest.main()