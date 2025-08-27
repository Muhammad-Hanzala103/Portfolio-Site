from flask import request
from flask_socketio import emit, join_room, leave_room
from . import webrtc_bp
from my_marketplace.app import socketio

@webrtc_bp.route('/webrtc')
def index():
    return "WebRTC signaling server"

@socketio.on('connect', namespace='/webrtc')
def on_connect():
    print('Client connected to WebRTC namespace')
    emit('status', {'msg': 'connected'})

@socketio.on('join', namespace='/webrtc')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'user {request.sid} joined room {room}'}, room=room)

@socketio.on('leave', namespace='/webrtc')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'user {request.sid} left room {room}'}, room=room)

@socketio.on('offer', namespace='/webrtc')
def on_offer(data):
    room = data['room']
    emit('offer', data, room=room, skip_sid=request.sid)

@socketio.on('answer', namespace='/webrtc')
def on_answer(data):
    room = data['room']
    emit('answer', data, room=room, skip_sid=request.sid)

@socketio.on('candidate', namespace='/webrtc')
def on_candidate(data):
    room = data['room']
    emit('candidate', data, room=room, skip_sid=request.sid)