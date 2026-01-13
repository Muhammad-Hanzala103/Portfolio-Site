import unittest
from my_marketplace.app import create_app, db
from my_marketplace.models import User, Conversation, Message
from config import TestConfig

class ChatTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Create test users
        self.user1 = User(name='user1', email='user1@example.com', role='buyer')
        self.user2 = User(name='user2', email='user2@example.com', role='seller')
        self.user1.set_password('password')
        self.user2.set_password('password')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_conversation_and_message(self):
        # Test creating a conversation
        conversation = Conversation(participants=f'{self.user1.id},{self.user2.id}')
        db.session.add(conversation)
        db.session.commit()
        self.assertIsNotNone(conversation.id)

        # Test sending a message
        message = Message(conversation_id=conversation.id, sender_id=self.user1.id, ciphertext='Hello, this is a test message.')
        db.session.add(message)
        db.session.commit()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.ciphertext, 'Hello, this is a test message.')

if __name__ == '__main__':
    unittest.main()