import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.on('status')
def on_status(data):
    print('Received status message:', data)
    sio.disconnect()

try:
    sio.connect('http://localhost:5000/webrtc', namespaces=['/webrtc'])
    sio.wait()
except Exception as e:
    print('Error:', e)