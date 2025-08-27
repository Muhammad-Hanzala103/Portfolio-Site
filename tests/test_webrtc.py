import unittest
from my_marketplace.app import create_app, db, socketio
from my_marketplace.models import User
from config import TestConfig
from my_marketplace.app.webrtc import routes as webrtc_routes

import time

class WebRTCSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a test user
        self.user = User(name='testuser', email='test@example.com', role='buyer')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_webrtc_smoke_test(self):
        client = socketio.test_client(self.app, namespace='/webrtc')
        socketio.sleep(1)
        
        # The connect handler should have been called, and sent a message.
        received = client.get_received('/webrtc')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'status')
        self.assertEqual(received[0]['args'][0]['msg'], 'connected')

        # Now check connection status
        self.assertTrue(client.is_connected('/webrtc'))

        # Join a room
        room_name = 'test-room'
        client.emit('join', {'room': room_name}, namespace='/webrtc')
        received = client.get_received('/webrtc')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'status')
        self.assertIn('joined', received[0]['args'][0]['msg'])

        # Leave the room
        client.emit('leave', {'room': room_name}, namespace='/webrtc')
        received = client.get_received('/webrtc')
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'status')
        self.assertIn('left', received[0]['args'][0]['msg'])

        client.disconnect('/webrtc')
        self.assertFalse(client.is_connected('/webrtc'))

if __name__ == '__main__':
    unittest.main()