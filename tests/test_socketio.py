import unittest
from my_marketplace.app import create_app, db, socketio
from my_marketplace.models import User, Conversation, Message
from config import TestConfig
import time

class SocketIOTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create test users
        self.user1 = User(name='user1', email='user1@example.com', role='buyer')
        self.user1.set_password('password')
        self.user2 = User(name='user2', email='user2@example.com', role='seller')
        self.user2.set_password('password')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

        # Create a conversation
        self.conversation = Conversation(participants=f'{self.user1.id},{self.user2.id}')
        db.session.add(self.conversation)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_socketio_connection(self):
        client = socketio.test_client(self.app)
        self.assertTrue(client.is_connected())
        client.disconnect()
        self.assertFalse(client.is_connected())

    def test_join_and_leave_conversation(self):
        client = socketio.test_client(self.app, namespace='/')
        self.assertTrue(client.is_connected())

        # Join conversation
        client.emit('join', {'conversation_id': self.conversation.id})
        received = client.get_received('/')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'status')

        # Leave conversation
        client.emit('leave', {'conversation_id': self.conversation.id})
        received = client.get_received('/')
        # There is no direct confirmation of leaving a room, so we just check that no error occurs

        client.disconnect()

    def test_send_and_receive_message(self):
        client1 = socketio.test_client(self.app, namespace='/')
        client2 = socketio.test_client(self.app, namespace='/')

        self.assertTrue(client1.is_connected())
        self.assertTrue(client2.is_connected())

        # client1 joins
        client1.emit('join', {'conversation_id': self.conversation.id})
        # client2 joins
        client2.emit('join', {'conversation_id': self.conversation.id})

        # client1 sends a message
        message_content = 'Hello, this is a test message!'
        client1.emit('send_message', {'conversation_id': self.conversation.id, 'content': message_content})

        # client2 should receive the message
        received = client2.get_received('/')
        self.assertGreater(len(received), 0)
        
        # The first received message is the status of client1 joining
        # The second received message is the status of client2 joining
        # The third should be the message from client1
        message_received = False
        for msg in received:
            if msg['name'] == 'new_message':
                self.assertEqual(msg['args'][0]['content'], message_content)
                message_received = True
                break
        self.assertTrue(message_received)

        client1.disconnect()
        client2.disconnect()

if __name__ == '__main__':
    unittest.main()